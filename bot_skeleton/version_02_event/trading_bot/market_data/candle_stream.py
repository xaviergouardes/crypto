from datetime import datetime, timedelta
from typing import Optional, Deque
from collections import deque

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import PriceUpdated, CandleClose, Candle, CandleHistoryReady

class CandleStream:
    """
    Construit des chandeliers (bougies) à partir d'un flux de prix
    et émet un événement CandleClose à la fin de chaque période.

    Peut être initialisée avec un historique de chandelles via CandleHistoryReady.
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.current_candle: Optional[Candle] = None
        self.candles: Deque[Candle] = deque()  # taille dictée par l'historique reçu
        self._initialized = False  # flag indiquant que l'historique est prêt
        self._period: Optional[float] = None  # durée d'une bougie en secondes
        self.symbol: Optional[str] = None      # symbole associé à ce flux

        # Souscription aux événements
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)

    async def on_history_ready(self, event: CandleHistoryReady):
        """Initialise le flux de bougies avec l'historique reçu."""
        if not event.candles:
            return

        self.symbol = event.candles[0].symbol.upper()  # symbole de la paire
        self.candles.extend(event.candles)
        self.current_candle = self.candles[-1]
        # Calcul de la période à partir de la dernière bougie du snapshot
        self._period = event.period.total_seconds()
        self._initialized = True  # l'historique est prêt, les ticks live peuvent être traités

    async def on_price_update(self, event: PriceUpdated) -> None:
        """Appelée à chaque tick de prix pour construire ou mettre à jour une bougie."""

        # Ignorer les ticks tant que l'historique n'est pas initialisé
        if not self._initialized or self._period is None:
            return

        # Vérification du symbole
        if event.symbol.upper() != self.symbol:
            raise ValueError(f"[CandleStream] Le symbole du flux {event.symbol.upper()} ne correspond pas à l'historique {self.symbol}")

        if self.current_candle is None:
            self._start_new_candle(event)
            return

        candle = self.current_candle

        # Si on dépasse la fin de la bougie -> on la clôture et on en démarre une nouvelle
        if event.timestamp >= candle.end_time:
            await self.event_bus.publish(CandleClose(
                symbol=event.symbol,
                candle=candle
            ))
            self._start_new_candle(event)
            # print(f"[CandleStream] Candle fermée : {candle}")
        else:
            # Mise à jour des valeurs OHLC
            candle.high = max(candle.high, event.price)
            candle.low = min(candle.low, event.price)
            candle.close = event.price

    # ─── Fonctions internes ─────────────────────────────────────────────

    def _start_new_candle(self, event: PriceUpdated) -> None:
        """Crée une nouvelle bougie alignée sur la période du snapshot."""
        if self._period is None:
            raise ValueError("La période n'est pas initialisée depuis l'historique")

        aligned_timestamp = datetime.fromtimestamp(
            (int(event.timestamp.timestamp()) // int(self._period)) * int(self._period)
        )

        start_time = aligned_timestamp
        end_time = start_time + timedelta(seconds=self._period)

        self.current_candle = Candle(
            symbol=event.symbol,
            open=event.price,
            high=event.price,
            low=event.price,
            close=event.price,
            start_time=start_time,
            end_time=end_time
        )
        self.candles.append(self.current_candle)
        # print(f"[CandleStream] Candle ouverte : {self.current_candle}")

    async def run(self):
        """Pas de loop nécessaire car tout est événementiel."""
        pass
