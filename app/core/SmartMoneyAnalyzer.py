from app.core.MarketStructureAnalyzer import MarketStructureAnalyzer
from app.core.LiquidityAnalyzer import LiquidityAnalyzer
from app.core.TechnicalIndicators import TechnicalIndicators
from app.core.DataHandler import DataHandler, Klines
import time
import pandas as pd
from ta.volatility import AverageTrueRange
from PlvLogger import Logger


class SmartMoneyAnalyzer:
    """Основной класс анализа
    """

    def __init__(self, dict_signal, intervals=None, limit=500):
        self.pair = dict_signal['pair']
        self.end_time = dict_signal['ts_start']
        self.intervals = ("5m", "1h", "1d") if intervals is None else intervals
        self.limit = limit
        self.data_handler = None
        self.dict_result = {'target': dict_signal['result']}
        self._init()
        self.logger = Logger('SmartMoneyAnalyzer', type_log='d').logger

    def _init(self):
        try:
            self.data_handler = DataHandler(symbol=self.pair, intervals=self.intervals, end_time=self.end_time,
                                            limit=self.limit)
        except Exception as e:
            self.logger.error(f"_init Error during initialization: {e}")
            self.data_handler = None

    @staticmethod
    def calculate_relative_atr(alt_df, btc_df, window=14):
        """Рассчитывает отношение ATR текущей монеты к ATR биткоина"""
        # Рассчитываем ATR для текущей монеты
        coin_atr = AverageTrueRange(high=alt_df['High'],
                                    low=alt_df['Low'],
                                    close=alt_df['Close'],
                                    window=window).average_true_range().iloc[-1]

        # Рассчитываем ATR для биткоина
        btc_atr = AverageTrueRange(high=btc_df['High'],
                                   low=btc_df['Low'],
                                   close=btc_df['Close'],
                                   window=window).average_true_range().iloc[-1]

        # Записываем отношение ATR монеты к ATR биткоина
        relative_atr_to_btc = -1
        if btc_atr != 0:
            relative_atr_to_btc = coin_atr / btc_atr
        return relative_atr_to_btc

    def handler_df(self, w_df, tf, n_df):
        # Обрабатываем
        w_df['is_pullback'] = w_df['swing_type'].isin(['HL', 'LH'])  # тип точки, преобразовываем в is_pullback
        w_df['is_uptrend'] = w_df['trend'] == 'uptrend'  # преобразуем trend_is_up = True or False
        w_df['cur_price_is_premium'] = w_df['cur_price_state'] == 'premium'  # текущая цена discount или премиум
        w_df['cur_price_is_discount'] = w_df['cur_price_state'] == 'discount'
        w_df['cur_volume_state_is_high'] = w_df['cur_volume_state'] == 'high'  # 20 к 80 свечек по объему
        w_df['cur_volume_state_is_low'] = w_df['cur_volume_state'] == 'low'  # 20 к 80 свечек по объему
        w_df['vwap_is_above'] = w_df['vwap_state'] == 'above'
        w_df['vwap_is_below'] = w_df['vwap_state'] == 'below'

        dict_last_kline = w_df.iloc[-1].to_dict()
        structural_points = w_df[w_df['swing_type'].notna()]
        dict_last_row = structural_points.iloc[-1].to_dict()

        for el in ('is_bos',  # слом на структурной точки
                   'is_repeated_bos',  # сразу 2 слома на структурной точки
                   'is_confirm',  # подтверждение тренда
                   'is_normal_pullback',  # коррекция от 50 до 75 процентов на структурной точке
                   'is_deep_pullback',  # коррекция от 75 до 100 процентов на структурной точке
                   'is_pullback',  # изменили структурные точки на коррекцию или рост/падение
                   'is_uptrend',  # Изменили тренд на рост? True or False
                   'momentum',  # momentum на структурную точку
                   'momentum_vol',  # momentum_vol на структурную точку
                   'momentum_price'):  # momentum_price на структурную точку
            self.dict_result[f"_{n_df}_{el}_{tf}"] = dict_last_row[el]

        # Тут собираем для последней свечки
        for el in ('diff_avg_vol',  # изменение среднего объема за 5 свечей к 100 свечкам
                   'cur_price_is_premium',  # Текущая цена premium?
                   'cur_price_is_discount',  # Текущая цена discount?
                   'action_ready',  # дублирующий признак, если рост и мы в discount, если падение то premium
                   'cur_volume_state_is_high',  # состояние объема, сравнивая последние 20% свечей с предыдущими 80%
                   'cur_volume_state_is_low',  # после структурной точки до текущей
                   'vwap_is_above',  # положение текущей цены относительно VWAP текущего движения
                   'vwap_is_below',  # положение текущей цены относительно VWAP текущего движения
                   'liquidity_ratio',  # ликвидность за стопами, важный показатель
                   'relative_liquidity_position',  # 0-1 ближайшая ликвидность относительно текущей точки, -1 нет ликвидности
                   'fvg_ratio',  # ликвидность имбалансов, важный показатель
                   'relative_fvg_position',  # 0-1 ближайшая fvg относительно текущей точки, -1 нет fvg
                   'rsi',
                   'ema',
                   'atr'):
            self.dict_result[f"_{n_df}_{el}_{tf}"] = dict_last_kline[el]

        if tf == '1h':
            # Получаем последние 24 свечи
            last_24h_alt = w_df.iloc[-24:]
            if self.data_handler.df_btc is None:
                self.dict_result[f"diff_btc_24_vol"] = -1
                return

            last_24h_btc = self.data_handler.df_btc.iloc[-24:]

            # Проверяем, достаточно ли у нас данных
            if len(last_24h_alt) < 24 or len(last_24h_btc) < 24:
                self.dict_result[f"diff_btc_24_vol"] = -1
                return

            relative_atr_to_btc = self.calculate_relative_atr(alt_df=w_df, btc_df=self.data_handler.df_btc)
            self.dict_result[f"relative_atr_to_btc"] = round(relative_atr_to_btc, 2)

            # Рассчитываем объем в долларах для каждой свечи и суммируем
            alt_24h_volume = (last_24h_alt['Volume'] * last_24h_alt['Close']).sum()
            btc_24h_volume = (last_24h_btc['Volume'] * last_24h_btc['Close']).sum()

            normalized_ratio = (alt_24h_volume / btc_24h_volume) * 100  # в процентах от объема BTC
            self.dict_result[f"diff_btc_24_vol"] = round(normalized_ratio, 2)

    async def main(self):
        if self.data_handler is None:
            return
        klines = await self.data_handler.get_ohlcv_data()
        if isinstance(klines, Klines) is False:
            return
        n_df = 1
        for tf in klines.v_intervals:
            tmp_df = getattr(klines, f"_{tf}", None)
            if isinstance(tmp_df, pd.DataFrame):
                ma_df = MarketStructureAnalyzer(tmp_df).main()
                if ma_df is None:
                    return
                lq_df = LiquidityAnalyzer(ma_df).main()
                if lq_df is None:
                    return
                w_df = TechnicalIndicators(lq_df).main()
                self.handler_df(w_df, tf, n_df)
                n_df += 1

        return self.dict_result

