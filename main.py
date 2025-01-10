import numpy as np
import pandas as pd
import logging
from typing import List, Tuple, Union, Dict


class SwingAnalyzer:
    def __init__(self, log_level=logging.INFO):
        """
        Инициализация анализатора свингов

        Parameters:
        log_level: уровень логирования
        """
        self.SWING_TYPES = {
            't_': 'temporary',  # временный свинг
            's_': 'strong',  # сильный свинг (в premium/discount)
            'w_': 'weak',  # слабый свинг
            'd_': 'double',  # двойной свинг
            'b_': 'boss',  # слом основной структуры (bos)
            'mb_': 'minor boss',  # слом внутренней структуры (mbos)
            'sms_': 'failure'  # неудачный свинг (failure swing)
        }

        self.setup_logger(log_level)

    def setup_logger(self, log_level: int) -> None:
        """Настройка логирования"""
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('swing_analyzer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('SwingAnalyzer')

    def is_premium_discount(self, df: pd.DataFrame, point_price: float, window: int = 20) -> str:
        """
        Определение находится ли точка в премиум/дискаунт зоне

        Parameters:
        df: DataFrame с историческими данными
        point_price: цена точки для проверки
        window: размер окна для расчета уровней

        Returns:
        str: 'premium', 'discount' или 'equilibrium'
        """
        look_back = df.iloc[-window:]
        highest = look_back['High'].max()
        lowest = look_back['Low'].min()

        equilibrium = lowest + (highest - lowest) * 0.5

        if point_price > equilibrium:
            self.logger.debug(f'Point {point_price} in premium zone (eq: {equilibrium})')
            return 'premium'
        elif point_price < equilibrium:
            self.logger.debug(f'Point {point_price} in discount zone (eq: {equilibrium})')
            return 'discount'
        else:
            self.logger.debug(f'Point {point_price} in equilibrium zone')
            return 'equilibrium'

    def process_swing_point(self, is_max: bool, is_min: bool,
                            time: int, high: float, low: float,
                            idx: int) -> Tuple[str, int, float, int]:
        """
        Обработка найденной точки свинга

        Parameters:
        is_max: является ли точка максимумом
        is_min: является ли точка минимумом
        time: время формирования точки
        high: максимум свечи
        low: минимум свечи
        idx: индекс свечи

        Returns:
        tuple: (тип_свинга, время, цена, индекс)
        """
        if is_max and is_min:
            self.logger.info(f'Found double swing at index {idx}')
            return ('d_High', time, high, idx)
        elif is_max:
            self.logger.info(f'Found high swing at index {idx}')
            return ('t_High', time, high, idx)
        else:
            self.logger.info(f'Found low swing at index {idx}')
            return ('t_Low', time, low, idx)

    def find_swing_points(self, df: pd.DataFrame, window: int = 5, type_extr: str = 'm') -> List[Tuple]:
        """
        Оптимизированная версия поиска свингов на 5 свечках

        Parameters:
        df: DataFrame с колонками High, Low, Close_time
        window: размер окна (по умолчанию 5)
        type_extr: тип определения экстремумов
            'm' - модифицированный (3-я свеча выше/ниже остальных)
            'n' - стандартный (с убыванием/возрастанием)

        Returns:
        list of tuples: [(тип_свинга, время, цена, индекс),...]
        """
        try:
            # Проверка входных данных
            if len(df) < window:
                self.logger.warning(f'DataFrame too small: {len(df)} < {window}')
                return []

            # Конвертируем в numpy массивы для оптимизации
            highs = df['High'].to_numpy()
            lows = df['Low'].to_numpy()
            times = df['Close_time'].to_numpy()

            result = []
            mid = window // 2

            # Проходим по всем возможным окнам
            for i in range(mid, len(df) - mid):
                # Получаем окно
                window_highs = highs[i - mid:i + mid + 1]
                window_lows = lows[i - mid:i + mid + 1]

                is_max = False
                is_min = False

                if type_extr == 'm':
                    # Модифицированная версия - центральная свеча выше/ниже остальных
                    is_max = (window_highs[mid] > np.max(window_highs[:mid]) and
                              window_highs[mid] > np.max(window_highs[mid + 1:]))
                    is_min = (window_lows[mid] < np.min(window_lows[:mid]) and
                              window_lows[mid] < np.min(window_lows[mid + 1:]))

                elif type_extr == 'n':
                    # Стандартная версия с убыванием/возрастанием
                    is_max = (window_highs[0] <= window_highs[1] < window_highs[2] >
                              window_highs[3] >= window_highs[4])
                    is_min = (window_lows[0] >= window_lows[1] > window_lows[2] <
                              window_lows[3] <= window_lows[4])
                else:
                    raise ValueError(f'Invalid type_extr: {type_extr}')

                if is_max or is_min:
                    # Обрабатываем найденную точку
                    point = self.process_swing_point(
                        is_max, is_min,
                        times[i],
                        window_highs[mid],
                        window_lows[mid],
                        i
                    )

                    # Проверяем зону
                    zone = self.is_premium_discount(df.iloc[:i + 1], point[2])

                    # Если точка в премиум/дискаунт - помечаем как сильную
                    if zone in ['premium', 'discount']:
                        point = ('s_' + point[0], *point[1:])

                    result.append(point)
                    self.logger.info(f'Added swing point: {point}')

            return result

        except Exception as e:
            self.logger.error(f'Error in find_swing_points: {str(e)}')
            raise

    def classify_swings(self, swings: List[Tuple], df: pd.DataFrame) -> List[Tuple]:
        """
        Классификация свингов и определение структуры

        Parameters:
        swings: список свингов [(тип, время, цена, индекс),...]
        df: исходный DataFrame для контекста

        Returns:
        list: классифицированные свинги
        """
        try:
            if len(swings) < 3:
                self.logger.warning('Not enough swings for classification')
                return swings

            classified = []

            for i, swing in enumerate(swings):
                if i < 2:
                    classified.append(swing)
                    continue

                prev_2 = classified[-2]
                prev_1 = classified[-1]
                curr = swing

                # Определяем тип структуры
                if curr[0].endswith('High'):
                    if curr[2] > prev_2[2]:  # Новый HH
                        new_swing = ('t_HH', *curr[1:])
                        self.logger.info(f'Classified Higher High at {curr[1]}')
                    else:  # Новый LH
                        new_swing = ('t_LH', *curr[1:])
                        self.logger.info(f'Classified Lower High at {curr[1]}')
                else:
                    if curr[2] < prev_2[2]:  # Новый LL
                        new_swing = ('t_LL', *curr[1:])
                        self.logger.info(f'Classified Lower Low at {curr[1]}')
                    else:  # Новый HL
                        new_swing = ('t_HL', *curr[1:])
                        self.logger.info(f'Classified Higher Low at {curr[1]}')

                classified.append(new_swing)

            return classified

        except Exception as e:
            self.logger.error(f'Error in classify_swings: {str(e)}')
            raise

    def detect_structure_break(self, swings: List[Tuple]) -> List[Tuple]:
        """
        Определение сломов структуры (bos и mbos)

        Parameters:
        swings: классифицированные свинги

        Returns:
        list: свинги с отмеченными сломами структуры
        """
        try:
            if len(swings) < 3:
                return swings

            result = []
            trend = None
            last_minor_break = None

            for i, swing in enumerate(swings):
                if i < 3:
                    result.append(swing)
                    continue

                prev_swing = result[-1]
                curr_swing = swing

                # Определяем тренд
                if not trend:
                    if 'HH' in curr_swing[0] or 'HL' in curr_swing[0]:
                        trend = 'up'
                    elif 'LL' in curr_swing[0] or 'LH' in curr_swing[0]:
                        trend = 'down'

                # Проверяем слом структуры
                if trend == 'up':
                    if 'LL' in curr_swing[0]:
                        if last_minor_break and last_minor_break > prev_swing[1]:
                            result.append(('mb_' + curr_swing[0], *curr_swing[1:]))
                            self.logger.info(f'Minor Break of Structure detected at {curr_swing[1]}')
                        else:
                            result.append(('b_' + curr_swing[0], *curr_swing[1:]))
                            self.logger.info(f'Break of Structure detected at {curr_swing[1]}')
                            last_minor_break = curr_swing[1]
                        trend = 'down'
                    else:
                        result.append(curr_swing)
                else:
                    if 'HH' in curr_swing[0]:
                        if last_minor_break and last_minor_break > prev_swing[1]:
                            result.append(('mb_' + curr_swing[0], *curr_swing[1:]))
                            self.logger.info(f'Minor Break of Structure detected at {curr_swing[1]}')
                        else:
                            result.append(('b_' + curr_swing[0], *curr_swing[1:]))
                            self.logger.info(f'Break of Structure detected at {curr_swing[1]}')
                            last_minor_break = curr_swing[1]
                        trend = 'up'
                    else:
                        result.append(curr_swing)

            return result

        except Exception as e:
            self.logger.error(f'Error in detect_structure_break: {str(e)}')
            raise

    def detect_sms(self, swings: List[Tuple]) -> List[Tuple]:
        """
        Определение Failure Swing (SMS - Shift Market Structure)

        Parameters:
        swings: список свингов с определенными сломами структуры

        Returns:
        list: свинги с отмеченными SMS
        """
        try:
            if len(swings) < 3:
                return swings

            result = []

            for i, swing in enumerate(swings):
                if i < 3:
                    result.append(swing)
                    continue

                prev_2 = result[-2]
                prev_1 = result[-1]
                curr = swing

                # Определяем failure swing
                if 'HH' in curr[0]:
                    if curr[2] < prev_2[2]:  # Не смог сделать новый максимум
                        new_swing = ('sms_' + curr[0], *curr[1:])
                        self.logger.info(f'SMS detected: Failed Higher High at {curr[1]}')
                        result.append(new_swing)
                    else:
                        result.append(curr)
                elif 'LL' in curr[0]:
                    if curr[2] > prev_2[2]:  # Не смог сделать новый минимум
                        new_swing = ('sms_' + curr[0], *curr[1:])
                        self.logger.info(f'SMS detected: Failed Lower Low at {curr[1]}')
                        result.append(new_swing)
                    else:
                        result.append(curr)
                else:
                    result.append(curr)

            return result

        except Exception as e:
            self.logger.error(f'Error in detect_sms: {str(e)}')
            raise

    def analyze_swings(self, df: pd.DataFrame) -> List[Tuple]:
        """
        Основной метод анализа

        Parameters:
        df: DataFrame с данными свечей

        Returns:
        list: полностью проанализированные свинги
        """
        try:
            self.logger.info('Starting swing analysis')

            # Находим базовые свинги
            self.logger.info('Finding basic swing points')
            swings = self.find_swing_points(df)

            # Классифицируем и определяем структуру
            self.logger.info('Classifying swings')
            swings = self.classify_swings(swings, df)

            # Определяем сломы структуры
            self.logger.info('Detecting structure breaks')
            swings = self.detect_structure_break(swings)

            # Определяем SMS
            self.logger.info('Detecting failure swings')
            swings = self.detect_sms(swings)

            self.logger.info('Swing analysis completed successfully')
            return swings

        except Exception as e:
            self.logger.error(f'Error in analyze_swings: {str(e)}')
            raise

    def get_current_structure(self, swings: List[Tuple]) -> Dict:
        """
        Получение текущего состояния структуры

        Parameters:
        swings: проанализированные свинги

        Returns:
        dict: текущее состояние структуры
        """
        try:
            if not swings:
                return {'trend': None, 'last_break': None}

            last_break = None
            trend = None

            # Идем с конца для поиска последнего слома
            for swing in reversed(swings):
                if 'b_' in swing[0] or 'mb_' in swing[0]:
                    last_break = swing
                    if 'HH' in swing[0]:
                        trend = 'up'
                    elif 'LL' in swing[0]:
                        trend = 'down'
                    break

            return {
                'trend': trend,
                'last_break': last_break
            }

        except Exception as e:
            self.logger.error(f'Error in get_current_structure: {str(e)}')
            raise
