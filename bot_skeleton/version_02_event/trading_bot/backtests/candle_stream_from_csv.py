import pandas as pd
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Deque
from zoneinfo import ZoneInfo
import math

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import Candle, CandleClose, CandleHistoryReady, PriceUpdated, StopBot, Price

class CandleStreamFromCSV:

    """
    Construit des chandeliers (bougies) à partir d'un flux de prix
    et émet un événement CandleClose à la fin de chaque période.

    Peut être initialisée avec un historique de chandelles via CandleHistoryReady.
    """

    def __init__(
            self, event_bus: EventBus, 
            csv_path: str, 
            symbol: str = "ETHUSDC",
            period=timedelta(minutes=1), 
            history_limit: int = 25
        ):
        self.event_bus = event_bus
        self.csv_path = csv_path
        self.symbol = symbol.upper()
        self.history_limit = history_limit
        self.period = period

        self.current_candle: Optional[Candle] = None
        self.candles: Deque[Candle] = deque()  # taille dictée par l'historique reçu
        self._initialized = False  # flag indiquant que l'historique est prêt

        # Souscription aux événements
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)

    async def on_history_ready(self, event: CandleHistoryReady):
        """Initialise le flux de bougies avec l'historique reçu."""
        if not event.candles:
            return

        self.symbol = event.candles[0].symbol.upper()  # symbole de la paire
        self.candles.extend(event.candles)
        self.current_candle = self.candles[-1]
        self._initialized = True  # l'historique est prêt, les ticks live peuvent être traités
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [CandleStream] Initialisation Terminée {len(self.candles)}")
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [CandleStream] Last Candle : {self.current_candle}")
        # self._dump_candles(self.candles)

    # async def on_price_update(self, event: PriceUpdated) -> None:
    #     """Appelée à chaque tick de prix pour construire ou mettre à jour une bougie."""
    #     print(f"[CandleStream] PriceUpdated recu : {event}")

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
                f"CandleStreamFromCSV - "
                f"{i:02d}. "
                f"[{start.strftime('%Y-%m-%d %H:%M:%S')} ➝ {end.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{c.symbol} | O:{c.open:.2f} H:{c.high:.2f} L:{c.low:.2f} C:{c.close:.2f}"
            )

    async def read_and_publish(self):
        """Pas de loop nécessaire car tout est événementiel."""

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
            df = df.iloc[self.history_limit:]

        for _, row in df.iterrows():
            start_time = row["timestamp"].to_pydatetime()
            # end_time = datetime.fromtimestamp( math.ceil(row["close_time"] / 1000) )
            end_time = start_time + self.period
            candle = Candle(
                symbol=self.symbol,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                start_time=start_time,
                end_time=end_time
            )
            await self.event_bus.publish(CandleClose(
                symbol=self.symbol,
                candle=candle
            ))

            # Envoyer un event Price avec le prix de Cloture
            await self.event_bus.publish(
                PriceUpdated(
                    Price(
                        symbol=self.symbol.upper(), 
                        price=candle.close, 
                        timestamp=datetime.now())
                    )
                )

            # print(
            #     f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [CandleStreamFromCSV] - new candles : "
            #     f"[{candle.start_time.strftime('%Y-%m-%d %H:%M:%S')} ➝ {candle.end_time.strftime('%Y-%m-%d %H:%M:%S')}] "
            #     f"{candle.symbol} | O:{candle.open:.2f} H:{candle.high:.2f} L:{candle.low:.2f} C:{candle.close:.2f}"
            # )

        # Envoyer un event Price avec le prix de Cloture
        await self.event_bus.publish(StopBot(timestamp=datetime.now()))
        
    async def run(self):
        # Lance la lecture du fichier et le publication des events
        await self.read_and_publish()

    
