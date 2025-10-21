# trading_bot/strategy/strategy_engine.py
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, SupportResistanceDetected, PriceUpdated, IndicatorUpdated

class StrategySynchronizedEngine:
    """Combine indicateurs et supports/résistances pour générer des signaux."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        # Valeurs en mémoire
        self.current_price = None
        self.supports = []
        self.resistances = []
        self.last_price = None
        self.last_indicators = {}

        # Flags pour savoir si on a reçu au moins un événement de chaque type
        self.received_price = False
        self.received_indicator = False
        self.received_support_resistance = False

        # Abonnements
        self.event_bus.subscribe(SupportResistanceDetected, self.on_support_resistance)
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator)
        self.event_bus.subscribe(PriceUpdated, self.on_price)

    async def on_support_resistance(self, event: SupportResistanceDetected):
        self.supports = event.supports
        self.resistances = event.resistances
        self.received_support_resistance = True

    async def on_indicator(self, event: IndicatorUpdated):
        self.last_indicators = event.values
        self.received_indicator = True

    async def on_price(self, event: PriceUpdated):
        self.current_price = event.price
        self.last_price = event.price.price
        self.received_price = True
        await self.evaluate_strategy()

    async def evaluate_strategy(self):
        # On ne calcule un signal que si tous les trois événements ont été reçus au moins une fois
        if not (self.received_price and self.received_indicator and self.received_support_resistance):
            return

        sma = self.last_indicators.get("sma")
        if sma is None:
            return

        signal = None
        if self.last_price > sma:
            signal = "BUY"
        elif self.last_price < sma:
            signal = "SELL"

        if signal:
            await self.event_bus.publish(TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                price=self.current_price,
                strategie = self.__class__.__name__,
                strategie_parameters = None,
                strategie_values = {
                    "sma": sma,
                },
            ))

        # Réinitialiser les flags pour resynchroniser avec les trois événements les plus frais
        self.received_price = False
        self.received_indicator = False
        self.received_support_resistance = False

    async def run(self):
        # Tout est événementiel
        pass