from app.core.AnalyzerBase import AnalyzerBase


class TechnicalIndicators(AnalyzerBase):
    """Технические индикаторы"""
    def calculate(self):
        self.calculate_atr()
        self.calculate_rsi()

    def calculate_atr(self):
        """Расчет ATR"""
        pass

    def calculate_rsi(self):
        """Расчет RSI"""
        pass