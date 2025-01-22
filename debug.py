import time

from app.core.DataHandler import DataHandler, Klines
from app.core.MarketStructureAnalyzer import MarketStructureAnalyzer
from app.core.LiquidityAnalyzer import LiquidityAnalyzer
import pandas as pd

import asyncio


# Пример использования
async def main():
    symbol = "SUIUSDT"
    intervals = ("1m", "5m", "1h", "4h", "1d")
    # intervals = ("1m",)
    handler = DataHandler(symbol, intervals, 500)
    klines: Klines = await handler.get_ohlcv_data()
    for tf in klines.v_intervals:
        cur_time = time.time()
        w_df = getattr(klines, f"_{tf}", None)
        if isinstance(w_df, pd.DataFrame):
            ma_df = MarketStructureAnalyzer(w_df).main()
            la_df = LiquidityAnalyzer(ma_df).main()
            setattr(klines, f"_{tf}", la_df)
            print(f"[{tf}] Done {cur_time - time.time()}")
        # if df is not None:
        #     df = self.find_swing_points(df)
        #     setattr(self.ohlcv_data, f"_{tf}", df)
    pass

# Запуск асинхронного кода
if __name__ == "__main__":
    asyncio.run(main())
