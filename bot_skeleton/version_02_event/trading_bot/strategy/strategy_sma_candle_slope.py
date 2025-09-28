from datetime import datetime

from collections import deque
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, PriceUpdated


class SmaBuffer:
    """Collecte des valeurs SMA jusqu'à ce que le buffer soit rempli."""
    def __init__(self, window_size: int):
        self.window_size = window_size
        self.buffer = deque(maxlen=window_size)

    def add(self, value: float):
        self.buffer.append(value)

    def is_ready(self):
        return len(self.buffer) == self.window_size

    def get_slope(self):
        if not self.is_ready():
            return None
        return self.buffer[-1] - self.buffer[0]

    def latest(self):
        return self.buffer[-1] if self.buffer else None

class StrategySmaCandleSlopeEngine:
    """
    Stratégie : génère des signaux selon la pente de la SMA calculée sur des bougies.
    - Achat si pente positive > threshold
    - Vente si pente négative < -threshold
    """

    def __init__(self, event_bus: EventBus, threshold: float = 0.05, window_size: int = 20):
        self.event_bus = event_bus
        self.threshold = threshold
        self.sma_buffer = SmaBuffer(window_size)
        self.state = "initializing"
        self.entry_price = None

        # Abonnement aux SMA des chandelles
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator)
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)

    async def on_indicator(self, event: IndicatorUpdated):
        """Réception d'une nouvelle SMA issue des bougies."""
        sma_value = event.values.get("sma_candle")
        if sma_value is None:
            return

        # Ajout dans l'historique
        self.sma_buffer.add(sma_value)

        # Phase d'initialisation
        if self.state == "initializing":
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySmaCandleSlopeEngine] En cours d'initialisation ... Collecte SMA : {len(self.sma_buffer.buffer)}/{self.sma_buffer.window_size}")

            if self.sma_buffer.is_ready():
                self.state = "ready"
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySmaCandleSlopeEngine] Initialisation terminée, stratégie opérationnelle.")
                return
            else:
                return

        # Phase de traitement
        await self.evaluate_strategy()

    async def on_price_update(self, event: PriceUpdated) -> None:
        """Réception d'un nouveau prix."""
        if self.state != "ready":
            return
        self.entry_price = event.price


    async def evaluate_strategy(self):
        """ Récupére la pente SMA si l'initialisation est fait sinon None """
        slope = self.sma_buffer.get_slope()
        if slope is None:
            return

        signal = None
        if slope > self.threshold:
            signal = "BUY"
        elif slope < -self.threshold:
            signal = "SELL"

        if signal:
            await self.event_bus.publish(TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                price=self.entry_price,  # on peut utiliser la dernière SMA comme proxy
            ))
            # print(f"[StrategySmaCandleSlope] Signal {signal} | slope={slope:.5f}")

    async def run(self):
        """Rien à faire ici : tout est événementiel."""
        pass
