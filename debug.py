from app.core.DataHandler import DataHandler, Klines
from app.core.MarketStructureAnalyzer import MarketStructureAnalyzer

import asyncio


# Пример использования
async def main():
    symbol = "BTCUSDT"
    intervals = ("1h", "4h", "1d")
    handler = DataHandler(symbol, intervals)
    klines: Klines = await handler.get_ohlcv_data()

    update_klines = MarketStructureAnalyzer(klines).analyze_multiple_timeframes()
    pass

# Запуск асинхронного кода
if __name__ == "__main__":
    asyncio.run(main())
