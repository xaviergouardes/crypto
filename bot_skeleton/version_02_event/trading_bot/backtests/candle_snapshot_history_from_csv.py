import pandas as pd
from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import Candle, CandleHistoryReady


class CandleSnapShotHistoryFromCsv:
    """
    Charge un snapshot historique de bougies depuis un fichier CSV
    et émet un événement CandleHistoryReady pour initialiser les indicateurs.

    Format CSV attendu :
    timestamp, open, high, low, close, volume
    """

    def __init__(
        self,
        event_bus: EventBus,
        csv_path: str,
        symbol: str = "ETHUSDC",
        period: timedelta = timedelta(minutes=1),
        history_limit: int = 25
    ):
        self.event_bus = event_bus
        self.csv_path = csv_path
        self.symbol = symbol.upper()
        self.period = period
        self.history_limit = history_limit
        self._fetched = False  # pour éviter une double lecture

    async def fetch_snapshot(self):
        """Lit le snapshot des chandelles depuis un fichier CSV et publie l'événement."""
        if self._fetched:
            return

        # Lecture du CSV
        df = pd.read_csv(self.csv_path)

        # Vérification des colonnes
        expected_cols = {"timestamp", "open", "high", "low", "close"}
        if not expected_cols.issubset(df.columns):
            raise ValueError(f"Le fichier CSV doit contenir les colonnes : {expected_cols}")

        # Conversion des timestamps
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        # Limite du nombre de bougies
        if self.history_limit and len(df) > self.history_limit:
            df = df.head(self.history_limit)

        candles: List[Candle] = []
        for _, row in df.iterrows():
            start_time = row["timestamp"].to_pydatetime()
            end_time = start_time + self.period
            candles.append(Candle(
                symbol=self.symbol,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                start_time=start_time,
                end_time=end_time
            ))

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [CandleSnapShotHistoryFromCsv] Snapshot CSV chargé ({len(candles)} bougies)")
        # self._dump_candles(candles)

        # Émission de l’événement CandleHistoryReady
        await self.event_bus.publish(CandleHistoryReady(
            symbol=self.symbol,
            timestamp=datetime.now(),
            period=self.period,
            candles=candles
        ))

        self._fetched = True

    def _dump_candles(self, candles):
        """Affiche les bougies pour debug."""
        # paris_tz = ZoneInfo("Europe/Paris")
        # print("📊 Liste des bougies (heure de Paris) :")
        for i, c in enumerate(candles, start=1):
            # start = c.start_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(paris_tz)
            # end = c.end_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(paris_tz)
            start = c.start_time.replace(tzinfo=ZoneInfo("UTC"))
            end = c.end_time.replace(tzinfo=ZoneInfo("UTC"))
            print(
                f"CandleSnapShotHistoryFromCsv - "
                f"{i:02d}. "
                f"[{start.strftime('%Y-%m-%d %H:%M:%S')} ➝ {end.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{c.symbol} | O:{c.open:.2f} H:{c.high:.2f} L:{c.low:.2f} C:{c.close:.2f}"
            )

    async def run(self):
        """Lance la construction du snapshot une seule fois."""
        await self.fetch_snapshot()
