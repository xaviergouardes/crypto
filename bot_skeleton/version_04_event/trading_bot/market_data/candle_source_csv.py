import pandas as pd
from typing import List, override
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from trading_bot.core.logger import Logger
from trading_bot.core.events import Candle, CandleHistoryReady, CandleClose
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
        super().__init__(event_bus)
        self.params = params
        self.logger.info(f"Initialisé - running={self.is_running()}")

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
    async def _warmup(self):
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

    async def join(self):
        if self._stream_task:
            await self._stream_task

    @override
    async def _stream(self):
        p = self.params
        df = self._read_csv()

        warmup_count = p["trading_system"]["warmup_count"]
        if len(df) > warmup_count:
            df = df.iloc[warmup_count:]
        else:
            raise ValueError(f"[CandleSourceCsv] Le CSV ne contient pas assez de bougies : len(df) < warmup_count")

        seconds = int(p["interval"][:-1]) * 60

        for _, row in df.iterrows():
            if self.should_stop(): 
                self.logger.info("Arrêt demandé — fin du flux CSV.")
                return
        
            candle = self._create_candle(row, seconds)
            await self.event_bus.publish(CandleClose(symbol=p["symbol"], candle=candle))

