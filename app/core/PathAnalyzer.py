class PathAnalyzer:
    def calculate_clear_path(self, current_price, target_price, obstacles):
        """Оценка чистоты пути до целевого уровня"""
        path_length = abs(target_price - current_price)
        clear_length = path_length - sum([abs(o - current_price) for o in obstacles])
        return clear_length / path_length

    def calculate_distances_to_levels(self, signal_row):
        """Расчет расстояний до уровней поддержки/сопротивления."""
        pass