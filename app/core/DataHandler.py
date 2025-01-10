import aiohttp
import asyncio
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional, ClassVar
from dataclasses import dataclass, field


@dataclass
class Klines:
    """
    Класс для хранения данных свечей по различным таймфреймам.
    Каждое поле представляет собой DataFrame для конкретного таймфрейма.
    """
    _1s: Optional[pd.DataFrame] = field(default=None)
    _1m: Optional[pd.DataFrame] = field(default=None)
    _3m: Optional[pd.DataFrame] = field(default=None)
    _5m: Optional[pd.DataFrame] = field(default=None)
    _15m: Optional[pd.DataFrame] = field(default=None)
    _30m: Optional[pd.DataFrame] = field(default=None)
    _1h: Optional[pd.DataFrame] = field(default=None)
    _2h: Optional[pd.DataFrame] = field(default=None)
    _4h: Optional[pd.DataFrame] = field(default=None)
    _6h: Optional[pd.DataFrame] = field(default=None)
    _8h: Optional[pd.DataFrame] = field(default=None)
    _12h: Optional[pd.DataFrame] = field(default=None)
    _1d: Optional[pd.DataFrame] = field(default=None)
    _3d: Optional[pd.DataFrame] = field(default=None)
    _1w: Optional[pd.DataFrame] = field(default=None)
    _1M: Optional[pd.DataFrame] = field(default=None)
    v_intervals: ClassVar[list[str]] = ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h",
                                        "1d", "3d", "1w", "1M"]


class DataHandler:
    BASE_URL = "https://api.binance.com/api/"

    def __init__(self, symbol: str, intervals: Tuple[str, ...]):
        self.symbol = symbol
        self.intervals = intervals
        self.klines = Klines()

        # Проверка интервалов
        for interval in intervals:
            if interval not in self.klines.v_intervals:
                raise ValueError(f"Недопустимый интервал: {interval}")

    async def fetch_klines(self, session, interval, limit=500):
        end_point = 'v3/klines'
        params = {"symbol": self.symbol,
                  "interval": interval,
                  "limit": limit}
        try:
            w_url = f"{self.BASE_URL}{end_point}"
            async with session.get(w_url, params=params) as response:
                response.raise_for_status()
                return interval, await response.json()
        except Exception as e:
            print(f"Ошибка при запросе данных для {interval}: {e}")
            return interval, None

    async def fetch_all_intervals(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_klines(session, interval) for interval in self.intervals]
            return await asyncio.gather(*tasks)

    @staticmethod
    def prepare_dataframe(klines):
        columns = ["Open_time", "Open", "High", "Low", "Close", "Volume", "Close_time", "Quote_asset_volume",
                   "Number_of_trades", "Taker_buy_base_volume", "Taker_buy_quote_volume", "Ignore"]
        df = pd.DataFrame(klines, columns=columns)
        df = df[["Open_time", "Open", "High", "Low", "Close", "Volume"]]
        df["Open_time"] = pd.to_datetime(df["Open_time"], unit="ms")
        df.set_index("Open_time", inplace=True)

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = df[col].astype(float)

        # Удаляем последнюю незакрытую свечу
        current_time = int(datetime.now().timestamp() * 1000)
        if df.index[-1].value >= current_time:
            df = df.iloc[:-1]

        return df

    async def get_ohlcv_data(self) -> Klines:
        results = await self.fetch_all_intervals()

        for interval, klines_data in results:
            if klines_data:
                df = self.prepare_dataframe(klines_data)
                if hasattr(self.klines, f"_{interval}"):
                    setattr(self.klines, f"_{interval}", df)
                else:
                    raise ValueError(f"Таймфрейм {interval} не поддерживается.")
        return self.klines

    def add_calculated_columns(self, new_data):
        """Добавление расчетных колонок в данные"""
        pass

    def normalize_distances(self, high, low, distances):
        """Нормализация расстояний в процентах"""
        # range_ = high - low
        # return [dist / range_ * 100 for dist in distances]
        pass


