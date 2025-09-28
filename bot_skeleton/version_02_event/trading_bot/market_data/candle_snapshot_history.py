import requests
from datetime import datetime, timedelta
from typing import List

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import Candle, CandleHistoryReady

class CandleSnapShotHistory:
    """
    Récupère un snapshot historique de bougies depuis Binance
    et émet un événement CandleHistoryReady pour l'initialisation des indicateurs.
    """

    BINANCE_INTERVALS = {
        timedelta(minutes=1): "1m",
        timedelta(minutes=3): "3m",
        timedelta(minutes=5): "5m",
        timedelta(minutes=15): "15m",
        timedelta(minutes=30): "30m",
        timedelta(hours=1): "1h",
    }

    def __init__(self, event_bus: EventBus, symbol: str = "ethusdc", period: timedelta = timedelta(minutes=1), history_limit: int = 25):
        self.event_bus = event_bus
        self.symbol = symbol.upper()
        self.period = period
        self.history_limit = history_limit
        self._fetched = False  # pour éviter de reconstruire plusieurs fois

    async def fetch_snapshot(self):
        """Récupère le snapshot des chandelles et publie l'événement."""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [CandleSnapShotHistory] Fetching snapshot for {self.symbol} ...")
        if self._fetched:
            return  # ne faire qu'une seule fois

        interval_str = self.BINANCE_INTERVALS.get(self.period)
        if interval_str is None:
            raise ValueError(f"Interval {self.period} non supporté")

        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": self.symbol,
            "interval": interval_str,
            "limit": self.history_limit
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        klines = response.json()

        candles: List[Candle] = []
        for k in klines:
            candle = Candle(
                symbol=self.symbol,
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                start_time=datetime.fromtimestamp(k[0] / 1000),
                end_time=datetime.fromtimestamp(k[6] / 1000)
            )
            candles.append(candle)

        # Publier l'événement avec l'historique des bougies
        await self.event_bus.publish(CandleHistoryReady(
            symbol=self.symbol,
            timestamp=datetime.utcnow(),
            period=self.period,
            candles=candles
        ))
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [CandleSnapShotHistory] Snapshot reçu {len(candles)}")

        self._fetched = True

    async def run(self):
        """Lance la construction du snapshot une seule fois."""
        await self.fetch_snapshot()
