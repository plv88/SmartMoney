from app.core.AnalyzerBase import AnalyzerBase
from app.core.DataHandler import DataHandler, Klines
import pandas as pd
from dataclasses import dataclass
from typing import Optional


class MarketStructureAnalyzer(AnalyzerBase):
    def __init__(self, ohlcv_data: Klines):
        self.ohlcv_data = ohlcv_data

    def find_swing_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Находит 5-ти свечные паттерны и определяет структурные точки.

        Колонки в результате:
        - is_swing_point: True если точка является структурной
        - swing_type: тип точки (HH, HL, LH, LL)
        - is_dual_extreme: True если точка является и максимумом и минимумом
        - trend: текущий тренд
        - bos: Break of Structure
        """
        # Инициализируем колонки
        for col in ['swing_type', 'is_dual_extreme', 'trend', 'bos', 'choch']:
            if col not in df.columns:
                df[col] = False if col in ['is_dual_extreme', 'bos', 'choch'] else None

        # У нас чистый df, структуры у нас тут не должно быть
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
            df.at[df.index[_idx], 'structure'] = _struc
            df.at[df.index[_idx], 'choch'] = _val

        return df

    def analyze_multiple_timeframes(self):
        """Анализ всех необходимых таймфреймов"""
        for tf in self.ohlcv_data.v_intervals:
            df = getattr(self.ohlcv_data, f"_{tf}", None)
            if df is not None:
                df = self.find_swing_points(df)
                setattr(self.ohlcv_data, f"_{tf}", df)


    # def enrich_signals(self, signals: pd.DataFrame, timeframes: list[str]) -> pd.DataFrame:
    #     """
    #     Обогащение сигналов данными о рыночной структуре.
    #     :param signals: DataFrame сигналов с колонками ['timestamp']
    #     :param timeframes: Список таймфреймов для обогащения
    #     :return: DataFrame с обогащенными сигналами
    #     """
    #     enriched_signals = signals.copy()
    #
    #     for tf in timeframes:
    #         df = getattr(self.ohlcv_data, f"_{tf}", None)
    #         if df is not None:
    #             for i, signal in enriched_signals.iterrows():
    #                 timestamp = signal['timestamp']
    #                 relevant_data = df[df['timestamp'] <= timestamp]
    #
    #                 if not relevant_data.empty:
    #                     last_row = relevant_data.iloc[-1]
    #                     enriched_signals.at[i, f'{tf}_trend'] = self.trends[tf]
    #                     enriched_signals.at[i, f'{tf}_bos'] = last_row['bos']
    #                     enriched_signals.at[i, f'{tf}_choch'] = last_row['choch']
    #
    #     return enriched_signals
    #
    # def process_single_signal(self, signal: dict, timeframes: list[str]) -> dict:
    #     """
    #     Обработка одного сигнала, обогащение данными о структуре рынка.
    #     :param signal: Словарь с информацией о сигнале {'timestamp': ..., 'pair': ..., 'direction': ...}
    #     :param timeframes: Список таймфреймов для анализа
    #     :return: Обогащенный сигнал с данными структуры рынка
    #     """
    #     enriched_signal = signal.copy()
    #
    #     for tf in timeframes:
    #         df = getattr(self.ohlcv_data, f"_{tf}", None)
    #         if df is not None:
    #             # Фильтруем данные свечей до момента сигнала
    #             relevant_data = df[df['timestamp'] <= signal['timestamp']]
    #
    #             if not relevant_data.empty:
    #                 # Берем последнюю строку для анализа
    #                 last_row = relevant_data.iloc[-1]
    #                 enriched_signal[f'{tf}_trend'] = self.trends.get(tf, "unknown")
    #                 enriched_signal[f'{tf}_bos'] = last_row.get('bos', False)
    #                 enriched_signal[f'{tf}_choch'] = last_row.get('choch', False)
    #
    #     return enriched_signal


    def calculate(self):
        """
        Реализация метода calculate() для анализа структуры рынка.
        """
        return
        # for interval in self.ohlcv_data.v_intervals:
        #     df = getattr(self.ohlcv_data, f"_{interval}", None)
        #     if df is None:
        #         continue
        #     df = self.find_swing_points(df)
        #     df = self.detect_bos_choch(df)
        #     setattr(self.ohlcv_data, f"_{interval}", df)
