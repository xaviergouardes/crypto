from collections import deque
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated

class StrategySmaSlopeEngine:
    """Stratégie : génère des signaux selon la pente moyenne de la SMA sur N ticks."""
    def __init__(self, event_bus: EventBus, threshold: float = 0.05, window_size: int = 20):
        self.event_bus = event_bus
        self.threshold = threshold
        self.window_size = window_size

        # Mémoire : historique des SMA
        self.sma_history = deque(maxlen=window_size)

        # Abonnement
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator)

    async def on_indicator(self, event: IndicatorUpdated):
        sma_value = event.values.get("sma")
        if sma_value is None:
            return

        # Ajout dans l'historique
        self.sma_history.append(sma_value)
        await self.evaluate_strategy()

    async def evaluate_strategy(self):
        # On ne calcule la pente que si on a suffisamment de points
        if len(self.sma_history) < self.window_size:
            return

        # Pente sur N ticks : dernier - plus ancien
        slope = self.sma_history[-1] - self.sma_history[0]
        signal = None

        if slope > self.threshold:
            signal = "BUY"
        elif slope < -self.threshold:
            signal = "SELL"

        if signal:
            await self.event_bus.publish(TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                price=self.sma_history[-1]  # on peut utiliser la dernière SMA comme proxy
            ))
            # print(f"[StrategySmaSlopeEngine] Signal {signal} | slope={slope:.5f} ")

    async def run(self):
        pass
