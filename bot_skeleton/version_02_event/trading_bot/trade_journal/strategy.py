# trading_bot/strategy/strategy_engine.py
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, SupportResistanceDetected, PriceUpdated, IndicatorUpdated

class StrategyEngine:
    """Combine indicateurs et supports/résistances pour générer des signaux."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        # Valeurs en mémoire
        self.supports = []
        self.resistances = []
        self.last_price = None
        self.last_indicators = {}

        # Abonnements
        self.event_bus.subscribe(SupportResistanceDetected, self.on_support_resistance)
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator)
        self.event_bus.subscribe(PriceUpdated, self.on_price)

    async def on_support_resistance(self, event: SupportResistanceDetected):
        self.supports = event.supports
        self.resistances = event.resistances

    async def on_indicator(self, event: IndicatorUpdated):
        self.last_indicators = event.values

    async def on_price(self, event: PriceUpdated):
        self.last_price = event.price
        await self.evaluate_strategy()

    async def evaluate_strategy(self):
        if self.last_price is None or not self.last_indicators:
            return

        sma = self.last_indicators.get("sma", None)
        if sma is None:
            return

        signal = None
        # Exemple simple : BUY si prix > SMA et proche du support
        # if self.supports and abs(self.last_price - self.supports[0]) < 0.5 and self.last_price > sma:
        if self.last_price > sma:
            signal = "BUY"
        # SELL si prix < SMA et proche de la résistance
        # elif self.resistances and abs(self.last_price - self.resistances[0]) < 0.5 and self.last_price < sma:
        elif self.last_price < sma:
            signal = "SELL"

        if signal:
            await self.event_bus.publish(TradeSignalGenerated(
                side=signal,
                confidence=1.0,  # confiance maximale pour la version simple
                price= self.last_price

            ))
            # print(f"[StrategyEngine] Signal généré : {signal} entry_price {self.last_price:.2f}")

    async def run(self):
        # Tout est événementiel
        pass
