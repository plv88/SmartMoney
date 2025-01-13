from app.core.DataHandler import Klines
import pandas as pd


class MarketStructureAnalyzer:
    def __init__(self, w_df):
        self.w_df = w_df

    @staticmethod
    def _calculate_candl_vol(df, start_idx, end_idx, include_start=False, include_end=True):
        mask = pd.Series(False, index=df.index)

        if include_start and include_end:
            mask[(df.index >= start_idx) & (df.index <= end_idx)] = True
        elif include_start and not include_end:
            mask[(df.index >= start_idx) & (df.index < end_idx)] = True
        elif not include_start and include_end:
            mask[(df.index > start_idx) & (df.index <= end_idx)] = True
        else:
            mask[(df.index > start_idx) & (df.index < end_idx)] = True

        segment = df[mask]
        return len(segment), segment['Volume'].sum()

    @staticmethod
    def calculate_volume_trend(df, short_window=5, long_window=100):
        # Средний объем за последние short_window свечей
        short_volume_mean = df['Volume'].iloc[-short_window:].mean()
        # Длинное окно (long_window), исключая последние short_window
        long_volume_mean = df['Volume'].iloc[-(long_window++short_window):-short_window].mean()

        # Рассчитываем соотношение
        df['diff_vol_avg'] = round(short_volume_mean / long_volume_mean, 2) if long_volume_mean != 0 else None

        return df

    def calculate_momentum(self, df: pd.DataFrame, structure_points) -> pd.DataFrame:
        """
        Рассчитывает моментум по свечам и объему для точек коррекции.
        """
        for i in range(2, len(structure_points)):
            curr_idx = structure_points.index[i]
            current_point = structure_points.iloc[i]
            current_trend = df.at[curr_idx, 'trend']

            if current_trend is None:
                continue

            prev_2_idx = structure_points.index[i - 2]
            prev_1_idx = structure_points.index[i - 1]

            # Для точек коррекции (HL в восходящем, LH в нисходящем)
            if ((current_trend == 'uptrend' and current_point['swing_type'] == 'HL') or
                    (current_trend == 'downtrend' and current_point['swing_type'] == 'LH')):
                # Рассчитываем метрики импульса и коррекции
                impulse_candles, impulse_volume = self._calculate_candl_vol(df, prev_2_idx, prev_1_idx)
                correction_candles, correction_volume = self._calculate_candl_vol(df, prev_1_idx, curr_idx)
                if correction_candles > 0:
                    df.at[curr_idx, 'momentum'] = round(impulse_candles / correction_candles, 1)
                if correction_volume > 0:
                    df.at[curr_idx, 'momentum_vol'] = round(impulse_volume / correction_volume, 1)
            elif ((current_trend == 'uptrend' and current_point['swing_type'] == 'HH') or
                    (current_trend == 'downtrend' and current_point['swing_type'] == 'LL')):
                # Рассчитываем метрики обратного импульса и коррекции
                b_correction_candles, b_correction_volume = self._calculate_candl_vol(df, prev_2_idx, prev_1_idx)
                b_impulse_candles, b_impulse_volume = self._calculate_candl_vol(df, prev_1_idx, curr_idx)
                if b_impulse_candles > 0:
                    df.at[curr_idx, 'momentum'] = round(b_correction_candles / b_impulse_candles, 2)
                if b_impulse_volume > 0:
                    df.at[curr_idx, 'momentum_vol'] = round(b_correction_volume / b_impulse_volume, 2)

        return df

    def calculate_trend_strength(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Комплексный анализ силы тренда.
        """

        # Расчет pullback'ов
        structure_points = df[df['swing_type'].notna()].copy()
        if len(structure_points) >= 3:
            df = self.calculate_momentum(df, structure_points)

        for i in range(2, len(structure_points)):
            curr_idx = structure_points.index[i]
            current_trend = df.at[curr_idx, 'trend']

            if current_trend is None:
                continue

            if current_trend == 'uptrend' and structure_points.iloc[i]['swing_type'] == 'HL':
                hl = structure_points.iloc[i - 2]['Low']
                hh = structure_points.iloc[i - 1]['High']
                current_price = structure_points.iloc[i]['Low']
                correction_percent = 100 * (hh - current_price) / (hh - hl)

                if correction_percent < 50:
                    df.at[curr_idx, 'is_light_pullback'] = True
                elif 50 <= correction_percent <= 75:
                    df.at[curr_idx, 'is_normal_pullback'] = True
                elif 75 < correction_percent < 100:
                    df.at[curr_idx, 'is_deep_pullback'] = True

            elif current_trend == 'downtrend' and structure_points.iloc[i]['swing_type'] == 'LH':
                lh = structure_points.iloc[i - 2]['High']
                ll = structure_points.iloc[i - 1]['Low']
                current_price = structure_points.iloc[i]['High']
                correction_percent = 100 - (100 * (lh - current_price) / (lh - ll))

                if correction_percent < 50:
                    df.at[curr_idx, 'is_light_pullback'] = True
                elif 50 <= correction_percent <= 75:
                    df.at[curr_idx, 'is_normal_pullback'] = True
                elif 75 < correction_percent < 100:
                    df.at[curr_idx, 'is_deep_pullback'] = True

        return df

    @staticmethod
    def analyze_market_structure(df: pd.DataFrame) -> pd.DataFrame:
        """
        Анализирует рыночную структуру, определяя текущие тренды, сломы структуры (is_bos) и подтверждения трендов (is_confirm).

        Args:
            df: DataFrame с колонкой 'swing_type', содержащей структурные точки:
                - HH (Higher High): восходящий максимум.
                - HL (Higher Low): восходящая впадина.
                - LH (Lower High): нисходящий максимум.
                - LL (Lower Low): нисходящая впадина.

        Returns:
            DataFrame с добавленными колонками:
                - 'trend': текущий тренд ('uptrend', 'downtrend').
                - 'is_bos': True, если обнаружен слом структуры (Break of Structure).
                - 'is_confirm': True, если подтвержден текущий тренд.
        """
        # Получаем только строки со структурными точками
        structure_points = df[df['swing_type'].notna()].copy()

        if len(structure_points) < 3:
            return df

        # Проходим по структурным точкам
        for i in range(2, len(structure_points)):
            curr_idx = structure_points.index[i]

            current = structure_points.iloc[i]['swing_type']
            previous = structure_points.iloc[i - 1]['swing_type']
            previous2 = structure_points.iloc[i - 2]['swing_type']

            # Определяем тренд и is_confirm - проверка по 3 точкам
            if previous2 == 'HH' and previous == 'HL' and current == 'HH':
                df.at[curr_idx, 'trend'] = 'uptrend'
                df.at[curr_idx, 'is_confirm'] = True

            elif previous2 == 'LL' and previous == 'LH' and current == 'LL':
                df.at[curr_idx, 'trend'] = 'downtrend'
                df.at[curr_idx, 'is_confirm'] = True

            # Определяем is_bos - проверка по 2 точкам
            if previous == 'HH' and current == 'LL':  # когда HL становится LL
                df.at[curr_idx, 'trend'] = 'downtrend'
                df.at[curr_idx, 'is_bos'] = True

            elif previous == 'LL' and current == 'HH':  # когда LH становится HH
                df.at[curr_idx, 'trend'] = 'uptrend'
                df.at[curr_idx, 'is_bos'] = True

        # Заполняем все пустые значения тренда последним известным трендом
        df['trend'] = df['trend'].ffill()

        return df

    def find_swing_points(self) -> pd.DataFrame:
        """
        Находит структурные точки на основе 5-свечных паттернов и классифицирует их на основе рыночной структуры.

        Args:
            df: DataFrame с колонками OHLC (Open, High, Low, Close) и индексами, представляющими свечи.

        Returns:
            DataFrame с добавленными колонками:
                - 'is_swing_point': True, если точка является структурной.
                - 'swing_type': тип точки ('HH', 'HL', 'LH', 'LL').
                - 'is_dual_extreme': True, если точка одновременно является максимумом и минимумом.
                - 'trend': текущий тренд ('uptrend', 'downtrend').
                - 'is_bos': True, если зафиксирован слом структуры (Break of Structure).
                - 'is_confirm': True, если тренд подтвержден.
        """
        # Инициализируем колонки
        for col in ['is_dual_extreme', 'is_bos', 'is_confirm', 'is_light_pullback', 'is_normal_pullback', 'is_deep_pullback']:
            if col not in df.columns:
                df[col] = False

        for col in ['swing_type', 'trend', 'momentum', 'momentum_vol', 'diff_vol_avg']:
            if col not in df.columns:
                df[col] = None

        # У нас тут чистый df, структуры у нас не должно быть
        if df['swing_type'].replace('', pd.NA).notna().any():
            raise ValueError(f"Должен быть чистый df")

        # Для каждой точки нам нужно 5 свечей
        lst_temp_structure = []
        for i in range(2, len(df)-2):
            window = df.iloc[i-2: i+3]

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
                df.at[df.index[i], 'is_dual_extreme'] = True
                continue  # Пропускаем двойные экстремумы как шум

            if not is_high and not is_low:
                continue

            if len(lst_temp_structure) < 3:
                # Если одновременно и максимум и минимум в самом начале работы, то пропускаем
                if is_high and is_low:
                    continue
                # Делаем от балды структуру
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

        for _struc, _val, _idx in lst_temp_structure[3:]:
            df.at[df.index[_idx], 'swing_type'] = _struc

        return df

    def main(self):
        self.find_swing_points()
        self.analyze_market_structure()
        self.calculate_trend_strength()
        self.calculate_volume_trend()



