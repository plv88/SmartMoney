from app.core.AnalyzerBase import AnalyzerBase


class OrderBlockAnalyzer(AnalyzerBase):
    """Анализ ордер блоков"""
    def calculate(self):
        self.identify_order_blocks()

    def identify_order_blocks(self):
        """Определение Order Blocks"""
        pass

    def check_breaker_blocks(self):
        """Проверка Breaker Blocks"""
        pass

    def check_mitigation_blocks(self):
        """Проверка Mitigation Blocks"""
        pass