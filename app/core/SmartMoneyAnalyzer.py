from app.core.MarketStructureAnalyzer import MarketStructureAnalyzer
from app.core.LiquidityAnalyzer import LiquidityAnalyzer
from app.core.OrderBlockAnalyzer import OrderBlockAnalyzer
from app.core.ImbalanceAnalyzer import ImbalanceAnalyzer
from app.core.TechnicalIndicators import TechnicalIndicators
from app.core.SessionAnalyzer import SessionAnalyzer


class SmartMoneyAnalyzer:
    """Основной класс анализа"""
    def __init__(self, signals_data, ohlcv_data):
        self.signals = signals_data
        self.ohlcv_data = ohlcv_data

        # Подключение аналитических модулей
        self.modules = {
            "market_structure": MarketStructureAnalyzer(ohlcv_data),
            "liquidity": LiquidityAnalyzer(ohlcv_data),
            "order_blocks": OrderBlockAnalyzer(ohlcv_data),
            "imbalances": ImbalanceAnalyzer(ohlcv_data),
            "indicators": TechnicalIndicators(ohlcv_data),
            "sessions": SessionAnalyzer(ohlcv_data)
        }

    def analyze(self):
        """Запуск всех модулей анализа"""
        results = {}
        for name, module in self.modules.items():
            module.calculate()
            results[name] = module.data
        return results

    def optimize_parameters(self):
        """Оптимизация параметров стратегии"""
        pass

    def generate_report(self):
        """Генерация отчета"""
        pass
