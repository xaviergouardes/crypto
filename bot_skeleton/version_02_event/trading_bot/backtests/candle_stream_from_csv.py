import pandas as pd
from datetime import datetime, timedelta, timezone
from collections import deque
from typing import Optional, Deque
from zoneinfo import ZoneInfo
import asyncio

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import Candle, CandleClose, CandleHistoryReady


class CandleStreamFromCSV:
    """
    Lit un fichier CSV de chandelles (bougies) et émet un événement CandleClose
    pour chaque ligne. Sert à rejouer un historique.

    Format attendu du CSV :
    timestamp, open, high, low, close, volume
    """

    def __init__(self, event_bus: EventBus, csv_path: str, symbol: str, period_seconds: int):
        self.event_bus = event_bus
        self.csv_path = csv_path
        self.symbol = symbol.upper()
        self.period_seconds = period_seconds
        self.candles: Deque[Candle] = deque()

    async def load_history(self):
        """Charge les bougies depuis le CSV et envoie CandleHistoryReady."""
        df = pd.read_csv(self.csv_path)

        # Vérifie la colonne de temps
        if "timestamp" not in df.columns:
            raise ValueError("Le fichier CSV doit contenir une colonne 'timestamp'")

        # Conversion en datetime UTC
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        # Construction des objets Candle
        self.candles = deque([
            Candle(
                symbol=self.symbol,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                start_time=row["timestamp"].to_pydatetime(),
                end_time=row["timestamp"].to_pydatetime() + timedelta(seconds=self.period_seconds)
            )
            for _, row in df.iterrows()
        ])

        await self.event_bus.publish(CandleHistoryReady(
            candles=list(self.candles),
            period=timedelta(seconds=self.period_seconds)
        ))

        print(f"[CandleStreamFromCSV] Historique chargé : {len(self.candles)} bougies ({self.symbol})")

    async def replay(self, delay: float = 0.0):
        """
        Émet un événement CandleClose pour chaque bougie lue.
        Si delay > 0, attend ce délai entre chaque émission (simulation temps réel).
        """
        if not self.candles:
            await self.load_history()

        for candle in self.candles:
            await self.event_bus.publish(CandleClose(
                symbol=self.symbol,
                candle=candle
            ))
            if delay > 0:
                await asyncio.sleep(delay)

        print(f"[CandleStreamFromCSV] Lecture terminée ({len(self.candles)} bougies envoyées).")
