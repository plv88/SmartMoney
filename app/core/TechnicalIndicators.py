from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator


class TechnicalIndicators:
    """Технические индикаторы"""

    def __init__(self, w_df):
        self.w_df = w_df
        self.last_idx = w_df.index[-1]

    def calculate_rsi(self, window=14):
        """Расчет RSI"""
        rsi_indicator = RSIIndicator(close=self.w_df['Close'], window=window)
        self.w_df.at[self.last_idx, 'rsi'] = round(rsi_indicator.rsi().iloc[-1], 2)

    def calculate_ema(self, window=20):
        ema_indicator = EMAIndicator(close=self.w_df['Close'], window=window)
        self.w_df.at[self.last_idx, 'ema'] = round(ema_indicator.ema_indicator().iloc[-1], 2)

    def calculate_atr(self, window=14):
        """Рассчитывает ATR только для последней свечи"""
        # Создаем ATR индикатор
        atr_indicator = AverageTrueRange(high=self.w_df['High'],
                                         low=self.w_df['Low'],
                                         close=self.w_df['Close'],
                                         window=window)
        # Рассчитываем ATR
        atr_values = atr_indicator.average_true_range()
        self.w_df.at[self.last_idx, 'atr'] = round(atr_values.iloc[-1], 2)

    def main(self):
        for col in ('atr', 'rsi', 'ema'):
            if col not in self.w_df.columns:
                self.w_df[col] = None
        self.calculate_rsi()
        self.calculate_ema()
        self.calculate_atr()
        return self.w_df
