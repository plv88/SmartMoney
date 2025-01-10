class AnalyzerBase:
    """
    Базовый класс для всех анализаторов.
    """

    def calculate(self):
        """
        Метод-заглушка, который должен быть переопределен в дочернем классе.
        """
        raise NotImplementedError("Метод 'calculate' должен быть реализован в подклассе.")