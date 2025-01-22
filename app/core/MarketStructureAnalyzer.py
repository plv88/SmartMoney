import pandas as pd
import numpy as np
from PlvLogger import Logger


class MarketStructureAnalyzer:
    def __init__(self, w_df):
        self.w_df = w_df.copy()
        self.structure_points = None
        self.logger = Logger('MarketStructureAnalyzer', type_log='d').logger

    @staticmethod
    def update_structure_points(func):
        """Декоратор для обновления структурных точек перед выполнением метода"""

        def wrapper(self, *args, **kwargs):
            self._update_structure_points()
            return func(self, *args, **kwargs)

        return wrapper

    def _update_structure_points(self):
        """Обновляет структурные точки"""
        self.structure_points = self.w_df[self.w_df['swing_type'].notna()].copy()

    @update_structure_points
    def mark_repeated_bos(self):
        """
        Обогащает w_df, добавляя колонку 'is_repeated_bos', которая указывает на повторный более значимый BOS.
        """
        # Перебираем строки от начала до конца
        # Проходим по структурным точкам
        for i in range(1, len(self.structure_points)):
            # Индексы текущей и предыдущей структурной точки
            prev_index = self.structure_points.index[i - 1]
            curr_index = self.structure_points.index[i]

            # Проверяем, если в предыдущей и текущей точках есть BOS
            if self.w_df.at[prev_index, 'is_bos'] and self.w_df.at[curr_index, 'is_bos']:
                # Помечаем текущую точку как повторный более значимый BOS
                self.w_df.at[curr_index, 'is_repeated_bos'] = True

    def _calculate_candl_vol(self, start_idx, end_idx, include_start=False, include_end=True):
        mask = pd.Series(False, index=self.w_df.index)

        if include_start and include_end:
            mask[(self.w_df.index >= start_idx) & (self.w_df.index <= end_idx)] = True
        elif include_start and not include_end:
            mask[(self.w_df.index >= start_idx) & (self.w_df.index < end_idx)] = True
        elif not include_start and include_end:
            mask[(self.w_df.index > start_idx) & (self.w_df.index <= end_idx)] = True
        else:
            mask[(self.w_df.index > start_idx) & (self.w_df.index < end_idx)] = True

        segment = self.w_df[mask]
        return len(segment), segment['Volume'].sum()

    def calculate_volume_trend(self, short_window=5, long_window=100):
        # Средний объем за последние short_window свечей
        short_volume_mean = self.w_df['Volume'].iloc[-short_window:].mean()
        # Длинное окно (long_window), исключая последние short_window
        long_volume_mean = self.w_df['Volume'].iloc[-(long_window++short_window):-short_window].mean()
        # Рассчитываем соотношение
        self.w_df['diff_avg_vol'] = round(short_volume_mean / long_volume_mean, 2) if long_volume_mean != 0 else None

    @update_structure_points
    def calculate_momentum(self):
        """
        Рассчитывает momentum по свечам и объему для точек коррекции.
        """
        for i in range(2, len(self.structure_points)):
            curr_idx = self.structure_points.index[i]
            current_point = self.structure_points.iloc[i]
            current_trend = self.w_df.at[curr_idx, 'trend']

            if current_trend is None:
                continue

            prev_2_idx = self.structure_points.index[i - 2]
            prev_1_idx = self.structure_points.index[i - 1]

            impulse_price_change = abs(self.w_df.at[prev_1_idx, 'Close'] - self.w_df.at[prev_2_idx, 'Close'])
            correction_price_change = abs(self.w_df.at[curr_idx, 'Close'] - self.w_df.at[prev_1_idx, 'Close'])

            # Для точек коррекции (HL в восходящем, LH в нисходящем)
            if ((current_trend == 'uptrend' and current_point['swing_type'] == 'HL') or
                    (current_trend == 'downtrend' and current_point['swing_type'] == 'LH')):
                # Рассчитываем метрики импульса и коррекции
                impulse_candles, impulse_volume = self._calculate_candl_vol(prev_2_idx, prev_1_idx)
                correction_candles, correction_volume = self._calculate_candl_vol(prev_1_idx, curr_idx)

                if correction_candles > 0:
                    self.w_df.at[curr_idx, 'momentum'] = round(impulse_candles / correction_candles, 1)
                if correction_volume > 0:
                    self.w_df.at[curr_idx, 'momentum_vol'] = round(impulse_volume / correction_volume, 1)
                if correction_price_change > 0:
                    self.w_df.at[curr_idx, 'momentum_price'] = round(impulse_price_change / correction_price_change, 2)
            elif ((current_trend == 'uptrend' and current_point['swing_type'] == 'HH') or
                    (current_trend == 'downtrend' and current_point['swing_type'] == 'LL')):
                # Рассчитываем метрики обратного импульса и коррекции
                b_correction_candles, b_correction_volume = self._calculate_candl_vol(prev_2_idx, prev_1_idx)
                b_impulse_candles, b_impulse_volume = self._calculate_candl_vol(prev_1_idx, curr_idx)

                if b_impulse_candles > 0:
                    self.w_df.at[curr_idx, 'momentum'] = round(b_correction_candles / b_impulse_candles, 2)
                if b_impulse_volume > 0:
                    self.w_df.at[curr_idx, 'momentum_vol'] = round(b_correction_volume / b_impulse_volume, 2)
                if correction_price_change > 0:
                    self.w_df.at[curr_idx, 'momentum_price'] = round(impulse_price_change / correction_price_change, 2)

    def _calc_correction_percent(self, dict_reached, idx, correction_percent):
        if 50 <= correction_percent <= 75:
            dict_reached['normal'] = True
        if 75 < correction_percent < 100:
            dict_reached['deep'] = True

        if dict_reached['normal']:
            self.w_df.at[idx, 'is_normal_pullback'] = True
        if dict_reached['deep']:
            self.w_df.at[idx, 'is_deep_pullback'] = True

    @update_structure_points
    def calculate_trend_strength_struct(self):
        """
        Комплексный анализ силы тренда с отслеживанием коррекций в реальном времени.
        """
        # Проходим по структурным точкам для определения зон коррекции
        for i in range(2, len(self.structure_points)):
            curr_idx = self.structure_points.index[i]
            prev_idx = self.structure_points.index[i - 1]
            current_trend = self.w_df.at[curr_idx, 'trend']

            if current_trend is None or self.structure_points.iloc[i]['swing_type'] in ('HH', 'LL'):
                continue

            # Определяем опорные точки для расчета коррекции
            if current_trend == 'uptrend' and self.structure_points.iloc[i]['swing_type'] == 'HL':
                hl = self.structure_points.iloc[i - 2]['Low']
                hh = self.structure_points.iloc[i - 1]['High']

                # Проходим по всем свечам между prev_idx и curr_idx
                mask = (self.w_df.index > prev_idx) & (self.w_df.index <= curr_idx)
                correction_section = self.w_df[mask].copy()

                dict_reached = {'normal': False, 'deep': False}
                for idx in correction_section.index:
                    current_price = self.w_df.at[idx, 'Low']
                    correction_percent = 100 * (hh - current_price) / (hh - hl)
                    self._calc_correction_percent(dict_reached, idx, correction_percent)

            elif current_trend == 'downtrend' and self.structure_points.iloc[i]['swing_type'] == 'LH':
                lh = self.structure_points.iloc[i - 2]['High']
                ll = self.structure_points.iloc[i - 1]['Low']

                # Проходим по всем свечам между prev_idx и curr_idx
                mask = (self.w_df.index > prev_idx) & (self.w_df.index <= curr_idx)
                correction_section = self.w_df[mask].copy()

                dict_reached = {'normal': False, 'deep': False}
                for idx in correction_section.index:
                    current_price = self.w_df.at[idx, 'High']
                    correction_percent = 100 - (100 * (lh - current_price) / (lh - ll))

                    self._calc_correction_percent(dict_reached, idx, correction_percent)

    # @update_structure_points
    # def calculate_trend_strength_dynamic(self):
    #     """
    #     Рассчитывает dynamic коррекцию от последней структурной точки до текущей свечи
    #     """
    #     # Получаем данные последней структурной точки
    #     last_swing_idx = self.structure_points.index[-1]
    #     last_swing = self.structure_points.iloc[-1]
    #     current_trend = last_swing['trend']
    #     swing_type = last_swing['swing_type']
    #
    #     if current_trend is None:
    #         self.logger.warning(f"calculate_trend_strength_dynamic: current_trend is None")
    #         return
    #
    #     reference_high = None
    #     reference_low = None
    #
    #     # Проверяем наличие свечей после последней структурной точки
    #     future_candles = self.w_df.index[self.w_df.index > last_swing_idx]
    #     # Определяем опорные точки в зависимости от тренда и типа последней структурной точки
    #     if current_trend == 'uptrend':
    #         if swing_type == 'HH':
    #             reference_high = last_swing['High']
    #             reference_low = self.structure_points.iloc[-2]['Low']
    #     elif current_trend == 'downtrend':
    #         if swing_type == 'LL':
    #             reference_high = self.structure_points.iloc[-2]['High']  # LH
    #             reference_low = last_swing['Low']
    #
    #     if reference_high is None or reference_low is None or reference_high == reference_low:
    #         return
    #
    #     dict_reached = {'normal': False, 'deep': False}
    #     for idx in future_candles:
    #         current_price = self.w_df.at[idx, 'Low'] if current_trend == 'uptrend' else self.w_df.at[idx, 'High']
    #         correction_percent = (100 * (reference_high - current_price) / (reference_high - reference_low)
    #                               if current_trend == 'uptrend'
    #                               else 100 - (100 * (reference_high - current_price) / (reference_high - reference_low)))
    #         self._calc_correction_percent(dict_reached, idx, correction_percent)

    def analyze_market_structure(self):
        """
        Анализирует рыночную структуру, определяя текущие тренды, сломы структуры (is_bos) и подтверждения трендов (is_confirm).

        Returns:
            DataFrame с добавленными колонками:
                - 'trend': текущий тренд ('uptrend', 'downtrend').
                - 'is_bos': True, если обнаружен слом структуры (Break of Structure).
                - 'is_confirm': True, если подтвержден текущий тренд.
        """
        # Проходим по структурным точкам
        for i in range(2, len(self.structure_points)):
            curr_idx = self.structure_points.index[i]

            current = self.structure_points.iloc[i]['swing_type']
            previous = self.structure_points.iloc[i - 1]['swing_type']
            previous2 = self.structure_points.iloc[i - 2]['swing_type']

            # Определяем тренд и is_confirm - проверка по 3 точкам
            if previous2 == 'HH' and previous == 'HL' and current == 'HH':
                self.w_df.at[curr_idx, 'trend'] = 'uptrend'
                self.w_df.at[curr_idx, 'is_confirm'] = True

            elif previous2 == 'LL' and previous == 'LH' and current == 'LL':
                self.w_df.at[curr_idx, 'trend'] = 'downtrend'
                self.w_df.at[curr_idx, 'is_confirm'] = True

            # Определяем is_bos - проверка по 2 точкам
            if previous == 'HH' and current == 'LL':  # когда HL становится LL
                self.w_df.at[curr_idx, 'trend'] = 'downtrend'
                self.w_df.at[curr_idx, 'is_bos'] = True

            elif previous == 'LL' and current == 'HH':  # когда LH становится HH
                self.w_df.at[curr_idx, 'trend'] = 'uptrend'
                self.w_df.at[curr_idx, 'is_bos'] = True

        # Заполняем все пустые значения тренда последним известным трендом, от старых к новым
        self.w_df['trend'] = self.w_df['trend'].ffill()

    def find_swing_points(self):
        # Для каждой точки нам нужно 5 свечей
        lst_temp_structure = []
        for i in range(2, len(self.w_df)-2):
            window = self.w_df.iloc[i-2: i+3]

            prev_high_1 = window.iloc[0]['High']
            prev_high_0 = window.iloc[1]['High']
            curr_high = window.iloc[2]['High']
            next_high_0 = window.iloc[3]['High']
            next_high_1 = window.iloc[4]['High']

            prev_low_1 = window.iloc[0]['Low']
            prev_low_0 = window.iloc[1]['Low']
            curr_low = window.iloc[2]['Low']
            next_low_0 = window.iloc[3]['Low']
            next_low_1 = window.iloc[4]['Low']

            # Modified подход к определению экстремумов
            is_high = prev_high_1 < curr_high and prev_high_0 < curr_high > next_high_0 and curr_high > next_high_1
            is_low = prev_low_1 > curr_low and prev_low_0 > curr_low < next_low_0 and curr_low < next_low_1

            # Отмечаем двойные экстремумы, пока не ставим какой у нас тренд
            if is_high and is_low:
                self.w_df.at[self.w_df.index[i], 'is_dual_extreme'] = True
                continue  # Пропускаем двойные экстремумы как шум

            if not is_high and not is_low:
                continue

            if len(lst_temp_structure) < 3:
                # Если одновременно и максимум и минимум в самом начале работы, то пропускаем
                if is_high and is_low:
                    continue
                # Делаем от балды структуру по найденному свингу
                if is_high:
                    lst_temp_structure = [('HH', curr_high, 0), ('HL', curr_high, 0), ('HH', curr_high, 0)]
                else:  # is_low выше у нас условие, что обязательно что-то должно быть
                    lst_temp_structure = [('LL', curr_low, 0), ('LH', curr_low, 0), ('LL', curr_low, 0)]
                continue
            match lst_temp_structure[-1][0]:  # смотрим последнюю точку
                case 'HH':
                    if is_high:
                        if curr_high > lst_temp_structure[-1][1]:
                            lst_temp_structure[-1] = ('HH', curr_high, i)
                    else:  # is_low
                        if curr_low < lst_temp_structure[-2][1]:
                            # Тут у нас слом структуры
                            lst_temp_structure.append(('LL', curr_low, i))
                        else:
                            lst_temp_structure.append(('HL', curr_low, i))

                case 'HL':
                    if is_high:
                        if curr_high > lst_temp_structure[-2][1]:
                            lst_temp_structure.append(('HH', curr_high, i))
                    else:  # is_low
                        if curr_low < lst_temp_structure[-3][1]:
                            # Тут у нас слом структуры
                            lst_temp_structure[-1] = ('LL', curr_low, i)
                        elif curr_low < lst_temp_structure[-1][1]:
                            lst_temp_structure[-1] = ('HL', curr_low, i)

                case 'LL':
                    if is_high:
                        if curr_high > lst_temp_structure[-2][1]:
                            # Тут у нас слом структуры
                            lst_temp_structure.append(('HH', curr_high, i))
                        else:
                            lst_temp_structure.append(('LH', curr_high, i))
                    else:  # is_low
                        if curr_low < lst_temp_structure[-1][1]:
                            lst_temp_structure[-1] = ('LL', curr_low, i)

                case 'LH':
                    if is_high:
                        if curr_high > lst_temp_structure[-3][1]:
                            # Тут у нас слом структуры
                            lst_temp_structure[-1] = ('HH', curr_high, i)
                        elif curr_high > lst_temp_structure[-1][1]:
                            lst_temp_structure[-1] = ('LH', curr_high, i)
                    else:  # is_low
                        if curr_low < lst_temp_structure[-2][1]:
                            lst_temp_structure.append(('LL', curr_low, i))

        # Теперь заносим найденные точки в w_df
        for _struc, _val, _idx in lst_temp_structure[3:]:
            self.w_df.at[self.w_df.index[_idx], 'swing_type'] = _struc

    @update_structure_points
    def analyze_vwap_position(self, threshold_normal=0.5):
        """
        Анализирует положение текущей цены относительно VWAP текущего движения.
        VWAP рассчитывается по всем закрытым свечам после последней структурной точки (не включая её).
        """
        # Определяем начало текущего движения
        last_structure_idx = self.structure_points.index[-1]

        # Убедимся, что индекс числовой
        # if not pd.api.types.is_numeric_dtype(self.w_df.index):
        #     self.w_df.index = pd.to_numeric(self.w_df.index, errors='raise')

        # Получаем все закрытые свечи после структурной точки (не включая её)
        movement_mask = self.w_df.index > last_structure_idx
        if not np.asarray(movement_mask).any():
            return

        # Рассчитываем VWAP для текущего движения с маской чтобы не менять наш w_df
        vol_price = self.w_df.loc[movement_mask, 'Close'] * self.w_df.loc[movement_mask, 'Volume']
        total_vol_price = vol_price.sum()
        total_volume = self.w_df.loc[movement_mask, 'Volume'].sum()

        vwap = total_vol_price / total_volume if total_volume > 0 else 0

        # Анализируем последнюю закрытую свечу
        current_idx = self.w_df.loc[movement_mask].index[-1]
        current_price = self.w_df.at[current_idx, 'Close']

        # Рассчитываем отклонение от VWAP в процентах
        if vwap > 0:
            percent_diff = ((current_price - vwap) / vwap) * 100

            if percent_diff > threshold_normal:  # Выше VWAP (умеренно или сильно)
                vwap_state = 'above'
            elif percent_diff < -threshold_normal:  # Ниже VWAP (умеренно или сильно)
                vwap_state = 'below'
            else:  # В пределах ± threshold_normal
                vwap_state = 'at_vwap'

            # Обновляем только состояние
            self.w_df.at[current_idx, 'vwap_state'] = vwap_state

    @update_structure_points
    def analyze_cur_volume_state(self):
        """
        Анализирует состояние объема, сравнивая последние 20% свечей с предыдущими 80%.
        Берет свечи после последней структурной точки (не включая её).

        Returns:
            DataFrame с обогащенной последней строкой:
                - volume_state: high/normal/low
                - volume_ratio: отношение объема последних 20% свечей к предыдущим 80%
        """
        # Определяем начало текущего движения
        last_structure_idx = self.structure_points.index[-1]

        # Получаем все свечи после структурной точки (не включая её)
        current_movement = self.w_df[self.w_df.index > last_structure_idx]

        # Проверяем минимальное количество свечей (минимум 5 для разделения 1/4)
        total_candles = len(current_movement)
        if total_candles < 5:
            return

        # Определяем количество свечей для последних 20%
        recent_candles = max(1, total_candles // 5)

        # Разделяем движение на два непересекающихся периода
        recent_period = current_movement.iloc[-recent_candles:]  # последние 20%
        previous_period = current_movement.iloc[:-recent_candles]  # предыдущие 80%

        # Рассчитываем суммарные объемы для каждого периода
        recent_volume = recent_period['Volume'].sum()
        previous_volume = previous_period['Volume'].sum()

        # Нормализуем объемы по количеству свечей
        avg_recent_volume = recent_volume / len(recent_period)
        avg_previous_volume = previous_volume / len(previous_period) if len(previous_period) > 0 else avg_recent_volume

        # Рассчитываем отношение средних объемов
        volume_ratio = avg_recent_volume / avg_previous_volume if avg_previous_volume > 0 else 1

        # Определяем состояние объема
        if volume_ratio > 1.5:
            volume_state = 'high'
        elif volume_ratio < 0.5:
            volume_state = 'low'
        else:
            volume_state = 'normal'

        # Обновляем только последнюю строку
        current_idx = current_movement.index[-1]
        self.w_df.at[current_idx, 'cur_volume_state'] = volume_state
        # self.w_df.at[current_idx, 'cur_volume_ratio'] = round(volume_ratio, 2)

    @update_structure_points
    def analyze_cur_price_position(self):
        """
        Анализирует положение текущей цены относительно последних двух структурных точек.

        Returns:
            DataFrame с обогащенной последней строкой:
                - relative_position: процентное положение между структурными точками
                - price_state: discount/neutral/premium
        """
        # Получаем последние две структурные точки
        if len(self.structure_points) < 2:
            return self.w_df

        last_two_points = self.structure_points.iloc[-2:]
        last_point = last_two_points.iloc[-1]  # предыдущая
        prev_point = last_two_points.iloc[-2]  # предыдущая предыдущей

        # Получаем текущую (последнюю) свечу
        current_idx = self.w_df.index[-1]

        # Рассчитываем Typical Price для текущей свечи
        typical_price = (self.w_df.at[current_idx, 'High'] +
                         self.w_df.at[current_idx, 'Low'] +
                         self.w_df.at[current_idx, 'Close']) / 3

        # Определяем текущий тренд из последней свечи
        current_trend = self.w_df.at[current_idx, 'trend']

        # Определяем high и low в зависимости от тренда и типа последней структурной точки
        if current_trend == 'uptrend':
            if last_point['swing_type'] == 'HH':
                range_high = last_point['High']
                range_low = prev_point['Low']  # HL
            else:  # HL
                range_high = prev_point['High']  # HH
                range_low = last_point['Low']
        else:  # downtrend
            if last_point['swing_type'] == 'LL':
                range_high = prev_point['High']  # LH
                range_low = last_point['Low']
            else:  # LH
                range_high = last_point['High']
                range_low = prev_point['Low']  # LL

        # Рассчитываем относительное положение только если есть диапазон
        if range_high != range_low:
            relative_pos = (typical_price - range_low) / (range_high - range_low) * 100

            # Базовое состояние цены
            if relative_pos < 25:
                price_state = 'discount'
            elif relative_pos > 75:
                price_state = 'premium'
            else:
                price_state = 'neutral'

            # Состояние готовности к действию
            action_ready = False
            if (current_trend == 'uptrend' and price_state == 'discount') or (current_trend == 'downtrend' and
                                                                              price_state == 'premium'):
                action_ready = True

            self.w_df.at[current_idx, 'cur_price_state'] = price_state
            self.w_df.at[current_idx, 'action_ready'] = action_ready

    def main(self):
        """ Находит структурные точки на основе 5-свечных паттернов и классифицирует их
        Returns:
            DataFrame с добавленными колонками:
                - 'swing_type': тип точки ('HH', 'HL', 'LH', 'LL').
                - 'is_dual_extreme': True, если точка одновременно является максимумом и минимумом.
                - 'trend': текущий тренд ('uptrend', 'downtrend').
                - 'is_bos': True, если зафиксирован слом структуры (Break of Structure).
                - 'is_confirm': True, если тренд подтвержден.
                - 'is_normal_pullback', 'is_deep_pullback' - коррекции
                - 'momentum', 'momentum_vol' по свечкам и по объему
                - 'diff_avg_vol' среднее за последних 5 свечек к среднему за последние 100 свечек
        """
        # Инициализируем колонки
        for col in ['is_dual_extreme', 'is_bos', 'is_repeated_bos', 'is_confirm', 'is_normal_pullback', 'is_deep_pullback']:
            if col not in self.w_df.columns:
                self.w_df[col] = False
        for col in ['swing_type', 'trend', 'momentum', 'momentum_vol', 'momentum_price', 'diff_avg_vol', 'cur_price_state',
                    'action_ready', 'cur_volume_state', 'vwap_state']:
            if col not in self.w_df.columns:
                self.w_df[col] = None
        try:
            self.find_swing_points()
            self._update_structure_points()
            if self.structure_points is None or len(self.structure_points) < 4:
                return None
            self.analyze_market_structure()
            self.calculate_trend_strength_struct()
            # self.calculate_trend_strength_dynamic()  # дублирующий признак
            self.calculate_momentum()
            self.calculate_volume_trend()
            self.mark_repeated_bos()
            # Считаем для текущей цены где мы
            self.analyze_cur_price_position()
            self.analyze_cur_volume_state()
            self.analyze_vwap_position()
        except Exception as e:
            self.logger.error(f"Error in main: {e}")
            return

        return self.w_df
