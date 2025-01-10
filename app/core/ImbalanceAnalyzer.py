from app.core.AnalyzerBase import AnalyzerBase


class ImbalanceAnalyzer(AnalyzerBase):
    """Анализ дисбалансов"""
    def calculate(self):
        self.find_fvg()

    def find_fvg(self):
        """Поиск FVG"""
        pass