from app.core.AnalyzerBase import AnalyzerBase


class SessionAnalyzer(AnalyzerBase):
    """Анализ торговых сессий"""

    def calculate(self):
        self.identify_session()
        self.check_kill_zones()

    def identify_session(self):
        """Определение текущей сессии (Asian/London/NY)"""
        pass

    def check_kill_zones(self):
        """Проверка Kill Zones"""
        pass