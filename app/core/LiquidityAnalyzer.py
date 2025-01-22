
import numpy as np
import pandas as pd
from PlvLogger import Logger


class LiquidityAnalyzer:
    """
    Надо думать над кол-вом свечей, и возможно я усложнил расчетами это про уровни стопов
    в имбалансе можно перемножать не заполненность на процент изменения цены
    """
    def __init__(self, w_df):
        self.w_df = w_df
        self.current_index = self.w_df.index[-1]
        self.logger = Logger('LiquidityAnalyzer', type_log='d').logger

    def find_liquidity_levels(self):
        """
        Определяет непробитые уровни ликвидности BSL и SSL по 3-свечным формациям.

        Добавляет в DataFrame колонки:
        - has_bsl (bool): True если есть непробитый уровень BSL над текущей свечой
        - has_ssl (bool): True если есть непробитый уровень SSL под текущей свечой
        """

        # Проходим по каждой свече, кроме первой и последней
        for i in range(1, len(self.w_df) - 1):
            # Получаем данные для 3 последовательных свечей
            prev_high = self.w_df.iloc[i - 1]['High']
            curr_high = self.w_df.iloc[i]['High']
            next_high = self.w_df.iloc[i + 1]['High']

            prev_low = self.w_df.iloc[i - 1]['Low']
            curr_low = self.w_df.iloc[i]['Low']
            next_low = self.w_df.iloc[i + 1]['Low']

            curr_idx = self.w_df.index[i]

            # Проверяем BSL паттерн (центральный максимум выше соседних)
            if prev_high < curr_high > next_high:
                # Получаем все будущие свечи и проверяем пробой
                future_data = self.w_df[self.w_df.index > curr_idx]
                if not (future_data['High'] > curr_high).any():
                    self.w_df.at[curr_idx, 'has_bsl'] = True

            # Проверяем SSL паттерн (центральный минимум ниже соседних)
            if prev_low > curr_low < next_low:
                # Получаем все будущие свечи и проверяем пробой
                future_data = self.w_df[self.w_df.index > curr_idx]
                if not (future_data['Low'] < curr_low).any():
                    self.w_df.at[curr_idx, 'has_ssl'] = True

        return self.w_df

    def calculate_liquidity_ratio(self, alpha=0.1):
        """
        Рассчитывает соотношение ликвидности выше/ниже текущей цены.

        Args:
            alpha (float): Коэффициент затухания для временной составляющей
        """

        # Рассчитываем текущую цену как среднюю
        current_price = (self.w_df.loc[self.current_index, 'High'] +
                         self.w_df.loc[self.current_index, 'Low'] +
                         self.w_df.loc[self.current_index, 'Close']) / 3

        # Рассчитываем амплитуду всего движения
        price_range = self.w_df['High'].max() - self.w_df['Low'].min()

        # Инициализируем суммы весов
        dict_L_above = {}
        dict_L_below = {}

        # Получаем индексы где есть уровни ликвидности
        bsl_indices = self.w_df[self.w_df['has_bsl']].index
        ssl_indices = self.w_df[self.w_df['has_ssl']].index

        # Обрабатываем BSL уровни
        for idx in bsl_indices:
            if idx == self.current_index:
                continue

            v_i = self.w_df.loc[idx:self.current_index, 'Volume'].sum()
            level_price = self.w_df.loc[idx, 'High']
            d_i = (level_price - current_price) / price_range
            t_i = len(self.w_df.loc[idx:self.current_index])
            time_decay = np.exp(-alpha * t_i)
            dict_L_above[idx] = {'price': level_price,
                                 'l_lev': (v_i / d_i) * time_decay,
                                 'weight': 1}

        # Обрабатываем SSL уровни
        for idx in ssl_indices:
            if idx == self.current_index:
                continue

            v_i = self.w_df.loc[idx:self.current_index, 'Volume'].sum()
            level_price = self.w_df.loc[idx, 'Low']
            d_i = (current_price - level_price) / price_range
            t_i = len(self.w_df.loc[idx:self.current_index])
            time_decay = np.exp(-alpha * t_i)
            dict_L_below[idx] = {'price': level_price,
                                 'l_lev': (v_i / d_i) * time_decay,
                                 'weight': 1}

        # Проверяем близкие уровни через сортировку
        threshold = price_range * 0.01

        # Для BSL
        if dict_L_above:
            sorted_above = sorted(dict_L_above.items(), key=lambda x: x[1]['price'])
            for i in range(len(sorted_above) - 1):
                curr_idx, curr_data = sorted_above[i]
                next_idx, next_data = sorted_above[i + 1]
                if abs(next_data['price'] - curr_data['price']) <= threshold:
                    dict_L_above[curr_idx]['weight'] = 1.5
                    dict_L_above[next_idx]['weight'] = 1.5

        # Для SSL
        if dict_L_below:
            sorted_below = sorted(dict_L_below.items(), key=lambda x: x[1]['price'])
            for i in range(len(sorted_below) - 1):
                curr_idx, curr_data = sorted_below[i]
                next_idx, next_data = sorted_below[i + 1]
                if abs(next_data['price'] - curr_data['price']) <= threshold:
                    dict_L_below[curr_idx]['weight'] = 1.5
                    dict_L_below[next_idx]['weight'] = 1.5

        # Рассчитываем итоговые суммы с учетом весов
        L_above = sum(level['l_lev'] * level['weight'] for level in dict_L_above.values())
        L_below = sum(level['l_lev'] * level['weight'] for level in dict_L_below.values())
        L_total = L_above + L_below
        if L_total != 0:
            liquidity_ratio = (L_above - L_below) / L_total
            self.w_df.at[self.current_index, 'liquidity_ratio'] = round(liquidity_ratio, 2)
        else:
            self.w_df.at[self.current_index, 'liquidity_ratio'] = -1

    def mark_fvg_in_dataframe(self, fvg_threshold=20):
        """
        Функция для поиска и маркировки бычьих и медвежьих fvg (FVG) в DataFrame.

        Args:
            fvg_threshold: отсеиваем маленькие fvg

        pd.DataFrame: Обогащенный DataFrame с колонками 'bullish_fvg' и 'bearish_fvg'.
        """
        # Проходим по DataFrame, начиная с третьей строки
        for i in range(2, len(self.w_df.index)):
            # Доступ к индексам первой, средней и третьей свечи
            first_idx = self.w_df.index[i - 2]
            second_idx = self.w_df.index[i - 1]
            third_idx = self.w_df.index[i]

            # Диапазон первой свечи
            second_range = self.w_df.at[second_idx, 'High'] - self.w_df.at[second_idx, 'Low']
            if second_range == 0:
                continue

            # Проверка на медвежий FVG
            if self.w_df.at[first_idx, 'Low'] > self.w_df.at[third_idx, 'High']:
                # Вычисляем величину FVG в процентах от диапазона первой свечи
                initial_fvg = (self.w_df.at[first_idx, 'Low'] - self.w_df.at[third_idx, 'High']) / second_range * 100

                # Проверяем будущие данные на перекрытие
                future_data = self.w_df[self.w_df.index > third_idx]
                if not (self.w_df.at[third_idx, 'High'] <= future_data['High']).any():
                    # Если он маленький, то пропускам
                    if initial_fvg < fvg_threshold:
                        continue
                    # Если FVG не перекрыт, записываем относительную величину
                    self.w_df.at[second_idx, 'bearish_fvg'] = round(initial_fvg, 2)
                    fvg_mid = (self.w_df.at[first_idx, 'Low'] + self.w_df.at[third_idx, 'High']) / 2
                    self.w_df.at[second_idx, 'fvg_mid'] = round(fvg_mid, 2)

            # Проверка на бычий FVG
            if self.w_df.at[first_idx, 'High'] < self.w_df.at[third_idx, 'Low']:
                # Вычисляем величину FVG в процентах от диапазона первой свечи
                initial_fvg = (self.w_df.at[third_idx, 'Low'] - self.w_df.at[first_idx, 'High']) / second_range * 100

                # Проверяем будущие данные на перекрытие
                future_data = self.w_df[self.w_df.index > third_idx]
                if not (self.w_df.at[third_idx, 'Low'] >= future_data['Low']).any():
                    # Если он маленький, то пропускам
                    if initial_fvg < fvg_threshold:
                        continue
                    # Если FVG не перекрыт, записываем относительную величину
                    self.w_df.at[second_idx, 'bullish_fvg'] = round(initial_fvg, 2)
                    fvg_mid = (self.w_df.at[first_idx, 'High'] + self.w_df.at[third_idx, 'Low']) / 2
                    self.w_df.at[second_idx, 'fvg_mid'] = round(fvg_mid, 2)

        bullish_volumes = self.w_df[['bullish_fvg', 'Volume']].dropna()
        bullish_volumes['result'] = bullish_volumes['bullish_fvg'] * bullish_volumes['Volume']
        L_above = bullish_volumes['result'].sum()

        bearish_volumes = self.w_df[['bearish_fvg', 'Volume']].dropna()
        bearish_volumes['result'] = bearish_volumes['bearish_fvg'] * bearish_volumes['Volume']
        L_below = bearish_volumes['result'].sum()

        # Общий объем
        L_total = L_above + L_below
        # Проверяем, есть ли данные для расчета
        if L_total != 0:
            # Вычисляем нормализованный коэффициент
            fvg_ratio = (L_above - L_below) / L_total
            # Записываем результат в последнюю строку датафрейма
            self.w_df.at[self.current_index, 'fvg_ratio'] = round(fvg_ratio, 2)
        else:
            self.w_df.at[self.current_index, 'fvg_ratio'] = -1

    def calculate_relative_liquidity_position(self):
        """
        Рассчитывает относительное положение текущей цены между ближайшими уровнями ликвидности.

        Returns:
            - relative_liquidity_position: float от 0 до 1, где
              0 - цена на уровне ближайшего SSL
              1 - цена на уровне ближайшего BSL
              - 1 - если не найдены уровни ликвидности
        """
        current_idx = self.w_df.index[-1]
        current_price = (self.w_df.at[current_idx, 'Close']+self.w_df.at[current_idx, 'Low']+self.w_df.at[current_idx, 'High']) / 3

        # Получаем все BSL уровни выше текущей цены
        bsl_levels = self.w_df[self.w_df['has_bsl'] & (self.w_df.index < current_idx) & (
                self.w_df['High'] > current_price)]['High']

        # Получаем все SSL уровни ниже текущей цены
        ssl_levels = self.w_df[self.w_df['has_ssl'] & (self.w_df.index < current_idx) & (
                self.w_df['Low'] < current_price)]['Low']

        # Если нет уровней, возвращаем None
        if bsl_levels.empty or ssl_levels.empty:
            self.w_df.at[current_idx, 'relative_liquidity_position'] = -1
            return

        # Находим ближайший BSL уровень (минимальный из тех, что выше)
        nearest_bsl = bsl_levels.min()

        # Находим ближайший SSL уровень (максимальный из тех, что ниже)
        nearest_ssl = ssl_levels.max()

        # Проверяем, что уровни образуют корректный диапазон
        if nearest_ssl >= nearest_bsl:
            self.w_df.at[current_idx, 'relative_liquidity_position'] = -1
            return

        # Рассчитываем относительную позицию
        total_range = nearest_bsl - nearest_ssl
        relative_position = (current_price - nearest_ssl) / total_range

        # Сохраняем результат
        self.w_df.at[current_idx, 'relative_liquidity_position'] = round(relative_position, 3)

    def calculate_relative_fvg_position(self):
        """
        Рассчитывает относительное положение текущей цены между ближайшими серединами FVG.

        Returns:
            Добавляет в DataFrame колонку:
            - relative_fvg_position: float от 0 до 1, где
              0 - цена на уровне ближайшей нижней середины FVG
              1 - цена на уровне ближайшей верхней середины FVG
              None - если не найдены подходящие FVG
        """
        current_idx = self.w_df.index[-1]
        current_price = (self.w_df.at[current_idx, 'Close'] + self.w_df.at[current_idx, 'Low'] + self.w_df.at[
            current_idx, 'High']) / 3

        # Получаем все FVG с их серединами до текущей свечи
        fvg_data = self.w_df[(self.w_df['fvg_mid'].notna()) & (self.w_df.index < current_idx)]['fvg_mid']

        # Находим ближайшие уровни выше и ниже текущей цены
        levels_above = fvg_data[fvg_data > current_price]
        levels_below = fvg_data[fvg_data < current_price]

        if levels_above.empty or levels_below.empty:
            self.w_df.at[current_idx, 'relative_fvg_position'] = -1
            return

        # Берем ближайшие уровни
        nearest_above = levels_above.min()
        nearest_below = levels_below.max()

        # Рассчитываем относительную позицию
        total_range = nearest_above - nearest_below
        if total_range == 0:
            self.w_df.at[current_idx, 'relative_fvg_position'] = -1
            return
        relative_position = (current_price - nearest_below) / total_range
        # Сохраняем результат
        self.w_df.at[current_idx, 'relative_fvg_position'] = round(relative_position, 3)

    def main(self):
        # Инициализируем колонки
        for col in ('has_bsl', 'has_ssl'):
            if col not in self.w_df.columns:
                self.w_df[col] = False
        for col in ('liquidity_ratio', 'relative_liquidity_position', 'bullish_fvg', 'bearish_fvg', 'fvg_mid',
                    'relative_fvg_position'):
            if col not in self.w_df.columns:
                self.w_df[col] = None
        try:
            self.find_liquidity_levels()
            self.calculate_liquidity_ratio()
            self.calculate_relative_liquidity_position()
            self.mark_fvg_in_dataframe()
            self.calculate_relative_fvg_position()
        except Exception as e:
            self.logger.error(f"main error: {e}")
            return
        return self.w_df
