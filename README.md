SmartMoney
├── app/
│   ├── core/
│   │   ├── AnalyzerBase.py         # Базовый класс для всех анализаторов
│   │   │   ├── __init__            # Инициализация Дополнительные данные могут передаваться через *args и **kwargs.
│   │   │   └── calculate()           # Метод-заглушка для вычислений, переопределяется в дочерних классах
│   │   │
│   │   ├── Klines                 # Класс для хранения данных свечей (OHLCV) по таймфреймам
│   │   │   ├── __init__()         # Инициализация объекта с таймфреймами
│   │   │   └── v_intervals        # Список поддерживаемых таймфреймов
│   │   ├── DataHandler            # Основной класс для обработки данных
│   │   │   ├── __init__(symbol, intervals)   # Инициализация с тикером и интервалами
│   │   │   ├── fetch_klines()     # Асинхронный запрос данных по заданному таймфрейму
│   │   │   ├── fetch_all_intervals()  # Асинхронная загрузка данных для всех интервалов
│   │   │   ├── prepare_dataframe(klines)    # Преобразование данных в DataFrame с проверкой
│   │   │   ├── get_ohlcv_data()   # Получение всех данных OHLCV
│   │   │   ├── add_calculated_columns(new_data)   # Добавление расчетных колонок к данным
│   │   │   └── normalize_distances(high, low, distances) # Нормализация расстояний в процентах
│   │   │
│   │   ├── ImbalanceAnalyzer.py    # Анализ дисбаланса, поиск FVG
│   │   │   ├── calculate()           # Основные вычисления для анализа дисбаланса
│   │   │   └── find_fvg()            # Поиск зон незаполненной ликвидности (Fair Value Gaps)
│   │   │
│   │   ├── LiquidityAnalyzer.py    # Анализ ликвидности, уровни ликвидности и кластеры объема
│   │   │   ├── calculate()           # Основные вычисления для анализа ликвидности
│   │   │   ├── find_liquidity_levels() # Определение ключевых уровней ликвидности
│   │   │   ├── analyze_volume_clusters() # Анализ кластеров объема
│   │   │   ├── check_sweep_levels()  # Проверка уровней “сбора стопов”
│   │   │   ├── calculate_level_strength(volume_at_level, avg_volume) # Расчет силы уровня
│   │   │   └── find_equal_highs_lows() # Поиск уровней с равными хайами/лоу
│   │   │
│   │   ├── MarketStructureAnalyzer.py # Анализ рыночной структуры, тренды и точки разворота
│   │   │   ├── calculate()           # Основные вычисления для анализа рыночной структуры
│   │   │   ├── find_swing_points(data, lookback=2) # Поиск экстремумов рынка
│   │   │   ├── detect_bos_choch(data) # Обнаружение Break of Structure (BOS) и Change of Character (CHoCH)
│   │   │   ├── detect_trends()       # Определение трендов
│   │   │   ├── enrich_signals(signals, market_data) # Обогащение сигналов дополнительными данными
│   │   │   └── calculate_discount_premium(data) # Расчет зон дисконта/премии
│   │   │
│   │   ├── OrderBlockAnalyzer.py   # Анализ ордер-блоков, поиск блоков и их подтверждение
│   │   │   ├── calculate()           # Основные вычисления для анализа ордер-блоков
│   │   │   ├── identify_order_blocks() # Определение ордер-блоков
│   │   │   ├── check_breaker_blocks() # Проверка блоков-пробоев (Breaker Blocks)
│   │   │   └── check_mitigation_blocks() # Проверка блоков-митигаций (Mitigation Blocks)
│   │   │
│   │   ├── PathAnalyzer.py         # Анализ пути цены, расчет до уровней
│   │   │   ├── calculate_clear_path(current_price, target_price, obstacles) # Расчет пути от текущей до целевой цены
│   │   │   └── calculate_distances_to_levels(signal_row) # Определение расстояния до ключевых уровней
│   │   │
│   │   ├── SessionAnalyzer.py      # Анализ рыночных сессий, зоны активности
│   │   │   ├── calculate()           # Основные вычисления для анализа рыночных сессий
│   │   │   ├── identify_session()    # Определение текущей рыночной сессии
│   │   │   └── check_kill_zones()    # Проверка зон активности (Kill Zones)
│   │   │
│   │   ├── SmartMoneyAnalyzer.py   # Анализ “умных денег”, оптимизация параметров
│   │   │   ├── __init__(signals_data, ohlcv_data) # Инициализация с данными сигналов и OHLCV
│   │   │   ├── analyze()             # Анализ данных “умных денег”
│   │   │   ├── optimize_parameters() # Оптимизация параметров анализа
│   │   │   └── generate_report()     # Генерация отчета
│   │   │
│   │   └── TechnicalIndicators.py  # Технические индикаторы, расчет RSI и ATR
│   │       ├── calculate()           # Основные вычисления для индикаторов
│   │       ├── calculate_atr()       # Расчет Average True Range (ATR)
│   │       └── calculate_rsi()       # Расчет Relative Strength Index (RSI)