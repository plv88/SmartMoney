import aiohttp
import asyncio
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional, ClassVar
from dataclasses import dataclass, field
from PlvLogger import Logger


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
    BASE_URL = "https://fapi.binance.com"

    def __init__(self, symbol: str, intervals: Tuple[str, ...], limit, end_time=None):
        self.symbol = symbol
        self.intervals = intervals
        self.klines = Klines()
        self.limit = limit
        self.end_time = end_time
        self.btc_task = None
        self.df_btc = None
        self.logger = Logger('DataHandler', type_log='d').logger
        # Проверка интервалов
        for interval in intervals:
            if interval not in self.klines.v_intervals:
                self.logger.error(f"Недопустимый интервал: {interval}")
                raise ValueError(f"Недопустимый интервал: {interval}")

    # async def fetch_klines(self, session, w_symbol, interval, limit, retries=3, backoff=1):
    #     end_point = '/fapi/v1/klines'
    #     params = {"symbol": w_symbol, "interval": interval, "limit": limit}
    #     if self.end_time:
    #         params["endTime"] = self.end_time
    #
    #     for attempt in range(1, retries + 1):
    #         try:
    #             w_url = f"{self.BASE_URL}{end_point}"
    #             async with session.get(w_url, params=params) as response:
    #                 response.raise_for_status()
    #                 return interval, await response.json()
    #         except aiohttp.ClientError as e:
    #             self.logger.warning(f"Attempt {attempt}/{retries}: ClientError for {w_symbol}-{interval}: {e}")
    #         except Exception as e:
    #             self.logger.error(f"Attempt {attempt}/{retries}: Unexpected error for {w_symbol}-{interval}: {e}")
    #
    #         if attempt < retries:
    #             await asyncio.sleep(backoff)
    #             backoff *= 2  # Удваиваем время ожидания
    #     self.logger.error(f"Failed to fetch data for {w_symbol}-{interval} after {retries} attempts.")
    #     return interval, None

    async def fetch_klines(self, session, w_symbol, interval, limit, retries=3, backoff=1):
        if session.closed:
            self.logger.error(f"Session closed for {w_symbol}-{interval}")
            return interval, None

        for attempt in range(1, retries + 1):
            try:
                _params = {"symbol": w_symbol, "interval": interval, "limit": limit}
                if self.end_time:
                    _params["endTime"] = self.end_time
                async with session.get(f"{self.BASE_URL}/fapi/v1/klines",
                                       params=_params,
                                       timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        return interval, await response.json()
                    self.logger.error(f"HTTP {response.status} for {w_symbol}-{interval}")

            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout for {w_symbol}-{interval}")
            except aiohttp.ClientError as e:
                self.logger.warning(f"ClientError attempt {attempt}/{retries}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error attempt {attempt}/{retries}: {e}")

            await asyncio.sleep(backoff * attempt)

        return interval, None

    # async def fetch_all_intervals(self):
    #     try:
    #         async with aiohttp.ClientSession() as session:
    #             self.btc_task = asyncio.create_task(self.fetch_klines(session=session, w_symbol="BTCUSDT", interval="1h", limit=100))
    #             tasks = [self.fetch_klines(session=session, w_symbol=self.symbol, interval=intr, limit=self.limit)
    #                      for intr in self.intervals]
    #             result = await asyncio.gather(*tasks)
    #             return result
    #     except Exception as e:
    #         self.logger.error(f"fetch_all_intervals Error: {e}")

    async def fetch_all_intervals(self):
        try:
            connector = aiohttp.TCPConnector(force_close=True)
            tasks = []
            async with aiohttp.ClientSession(connector=connector) as session:
                # Create BTC task first self, session, w_symbol, interval, limit, retries=3, backoff=1
                tasks.append(asyncio.create_task(self.fetch_klines(session=session,
                                                                   w_symbol="BTCUSDT",
                                                                   interval="1h",
                                                                   limit=100)))
                # Add other tasks
                tasks.extend([asyncio.create_task(self.fetch_klines(session=session,
                                                                    w_symbol=self.symbol,
                                                                    interval=intr,
                                                                    limit=self.limit)) for intr in self.intervals])
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results
        except Exception as e:
            self.logger.error(f"fetch_all_intervals Error: {e}")

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

    async def get_ohlcv_data(self):
        results = await self.fetch_all_intervals()
        if not results:
            return

        for interval, klines_data in results[1:]:
            if klines_data:
                df = self.prepare_dataframe(klines_data)
                if hasattr(self.klines, f"_{interval}"):
                    setattr(self.klines, f"_{interval}", df)
                else:
                    self.logger.warning(f"get_ohlcv_data таймфрейм {interval} не поддерживается.")
                    return
        try:
            self.df_btc = self.prepare_dataframe(results[0][1])
        except Exception as e:
            self.logger.error(f"get_ohlcv_data BTC Error: {e}")
            return
        return self.klines
