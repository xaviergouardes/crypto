import pandas as pd
from typing import List, override
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from trading_bot.core.logger import Logger
from trading_bot.core.events import Candle, CandleHistoryReady, Price, CandleClose
from trading_bot.market_data.candle_source import CandleSource
from trading_bot.core.event_bus import EventBus

class CandleSourceCsv(CandleSource):
    """
    Source de données basée sur un fichier CSV.
    Fournit les bougies soit en bloc (warmup),
    soit sous forme de flux simulé (stream).
    """
    logger = Logger.get("CandleSourceCsv")

    REQUIRED_COLS = {"timestamp", "open", "high", "low", "close", "volume"}

    def __init__(self, event_bus: EventBus, params: dict):
        self.event_bus = event_bus
        self.params = params

    def _read_csv(self) -> pd.DataFrame:
        """Lit le CSV et convertit les timestamps en datetime UTC."""
        df = pd.read_csv(self.params["path"])
        if not self.REQUIRED_COLS.issubset(df.columns):
            raise ValueError(f"[CandleSourceCsv] Le CSV doit contenir les colonnes : {self.REQUIRED_COLS}")
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df

    def _create_candle(self, row, seconds) -> Candle:
        start_time = row["timestamp"].to_pydatetime()
        end_time = start_time + timedelta(seconds=seconds)
        return Candle(
            symbol=self.params["symbol"],
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
            start_time=start_time,
            end_time=end_time
        )
    
    @override
    async def warmup(self):
        p = self.params
        df = self._read_csv()

        # Limite du nombre de bougies
        warmup_count = p["trading_system"]["warmup_count"]
        if warmup_count and len(df) > warmup_count:
            df = df.head(warmup_count)

        seconds = int(p["interval"][:-1]) * 60
        candles: List[Candle] = [self._create_candle(row, seconds) for _, row in df.iterrows()]

        self.logger.info(f"Snapshot CSV chargé ({len(candles)} bougies)")

        await self.event_bus.publish(
            CandleHistoryReady(
                symbol=p["symbol"],
                timestamp=datetime.now(),
                period=p["interval"],
                candles=candles
            )
        )

    @override
    async def stream(self):
        p = self.params
        df = self._read_csv()

        warmup_count = p["trading_system"]["warmup_count"]
        if len(df) > warmup_count:
            df = df.iloc[warmup_count:]
        else:
            raise ValueError(f"[CandleSourceCsv] Le CSV ne contient pas assez de bougies : len(df) < warmup_count")

        seconds = int(p["interval"][:-1]) * 60

        for _, row in df.iterrows():
            candle = self._create_candle(row, seconds)
            await self.event_bus.publish(CandleClose(symbol=p["symbol"], candle=candle))

    def _dump_candles(self, candles):
        """Affiche les bougies pour debug."""
        for i, c in enumerate(candles, start=1):
            start = c.start_time.replace(tzinfo=ZoneInfo("UTC"))
            end = c.end_time.replace(tzinfo=ZoneInfo("UTC"))
            print(
                f"CandleSourceCsv - "
                f"{i:02d}. "
                f"[{start.strftime('%Y-%m-%d %H:%M:%S')} ➝ {end.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{c.symbol} | O:{c.open:.2f} H:{c.high:.2f} L:{c.low:.2f} C:{c.close:.2f} V:{c.volume:.2f}"
            )
