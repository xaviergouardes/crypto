# trading_bot/indicators/indicator_engine.py
from collections import deque
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import PriceUpdated, IndicatorUpdated

class IndicatorEngine:
    """Calcule les indicateurs techniques à partir des prix."""

    def __init__(self, event_bus: EventBus, window: int = 25):
        self.event_bus = event_bus
        self.window = window
        self.prices = deque(maxlen=window)
        # S'abonner aux prix
        self.event_bus.subscribe(PriceUpdated, self.on_price)

    async def on_price(self, event: PriceUpdated):
        self.prices.append(event.price.price)
        if len(self.prices) < self.window:
            return  # pas assez de données pour calculer l'indicateur

        # Calcul d'indicateurs simples
        sma = sum(self.prices) / len(self.prices)
        momentum = self.prices[-1] - self.prices[0]

        # Publier uniquement les valeurs calculées
        await self.event_bus.publish(IndicatorUpdated(
            symbol=event.price.symbol,
            timestamp=event.price.timestamp.timestamp(),
            values={"sma": sma, "momentum": momentum}
        ))
        # print(f"[IndicatorEngine] SMA: {sma:.2f}, Momentum: {momentum:.2f}")

    async def run(self):
        # Tout est événementiel, rien à faire ici
        pass
