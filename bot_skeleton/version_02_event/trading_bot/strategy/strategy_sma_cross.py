# trading_bot/strategy/strategy_engine.py
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, SupportResistanceDetected, PriceUpdated, IndicatorUpdated

class StrategySmaCrossEngine:
    """Combine indicateurs et supports/résistances pour générer des signaux."""
    def __init__(self, event_bus: EventBus, threshold: float = 0.01):
        self.event_bus = event_bus

        self.threshold = threshold  # tolérance pour éviter les faux signaux
        # Valeurs en mémoire
        self.last_price = None
        self.last_sma = None
        self.prev_price = None
        self.prev_sma = None

        # Flags pour savoir si on a reçu au moins un événement de chaque type
        self.received_price = False
        self.received_indicator = False

        # Abonnements
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator)
        self.event_bus.subscribe(PriceUpdated, self.on_price)

    async def on_indicator(self, event: IndicatorUpdated):
        self.last_sma = event.values.get("sma")
        self.received_indicator = True
        await self.evaluate_strategy()

    async def on_price(self, event: PriceUpdated):
        self.last_price = event.price.price
        self.received_price = True
        await self.evaluate_strategy()

    async def evaluate_strategy(self):
        # On ne calcule un signal que si tous les trois événements ont été reçus au moins une fois
        if not (self.received_price and self.received_indicator):
            return

        # On ne calcule le signal que si on a à la fois prix et SMA
        if self.prev_price is None or self.prev_sma is None:
            # Initialisation pour le prochain tick
            self.prev_price = self.last_price
            self.prev_sma = self.last_sma
            return

        # print(f"[StrategySynchronizedEngine] self.prev_price={self.prev_price}, self.prev_sma={self.prev_sma}, self.last_price={self.last_price}, self.last_sma={self.last_sma}")
        signal = None
        # Signal BUY : prix croise SMA à la hausse
        if (self.prev_price <= self.prev_sma - self.threshold) and (self.last_price > self.last_sma + self.threshold):
            signal = "BUY"
        # Signal SELL : prix croise SMA à la baisse
        elif (self.prev_price >= self.prev_sma + self.threshold) and (self.last_price < self.last_sma - self.threshold):
            signal = "SELL"

        if signal:
            await self.event_bus.publish(TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                price=self.last_price
            ))
            # print(f"[StrategySynchronizedEngine] Generated signal: {signal} => self.prev_price={self.prev_price}, self.prev_sma={self.prev_sma}, self.last_price={self.last_price}, self.last_sma={self.last_sma}")

        # Mettre à jour les valeurs précédentes pour le prochain tick
        self.prev_price = self.last_price
        self.prev_sma = self.last_sma

        # Réinitialiser les flags pour resynchroniser avec les trois événements les plus frais
        self.received_price = False
        self.received_indicator = False

    async def run(self):
        # Tout est événementiel
        pass