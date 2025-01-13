from app.core.DataHandler import DataHandler, Klines
from app.core.MarketStructureAnalyzer import MarketStructureAnalyzer

import asyncio


# Пример использования
async def main():
    symbol = "SUIUSDT"
    intervals = ("5m", "1h", "4h", "1d")
    # intervals = ("1m",)
    handler = DataHandler(symbol, intervals, 600)
    klines: Klines = await handler.get_ohlcv_data()

    MarketStructureAnalyzer(klines)
    # n_df = klines._1m[klines._1m['swing_type'].notna()]

    for tf in klines.v_intervals:
        w_df = getattr(klines, f"_{tf}", None)
        if w_df:
            setattr(klines, f"_{tf}", MarketStructureAnalyzer(w_df))
        # if df is not None:
        #     df = self.find_swing_points(df)
        #     setattr(self.ohlcv_data, f"_{tf}", df)
    pass

# Запуск асинхронного кода
if __name__ == "__main__":
    asyncio.run(main())
