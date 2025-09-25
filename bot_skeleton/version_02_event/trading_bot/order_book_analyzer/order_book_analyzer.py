# trading_bot/order_book/order_book_analyzer.py
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import OrderBookUpdated, SupportResistanceDetected

class OrderBookAnalyzer:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        # S'abonner à tous les updates du carnet
        self.event_bus.subscribe(OrderBookUpdated, self.on_order_book)
        # Liste de supports et résistances (on peut ajouter plus tard)
        self.supports: list[float] = []
        self.resistances: list[float] = []

    async def on_order_book(self, event: OrderBookUpdated):
        if not event.bids or not event.asks:
            return

        # Support = moyenne des 3 meilleurs bids
        top_bids = event.bids[:3]
        support = sum([price for price, qty in top_bids]) / len(top_bids)
        self.supports = [support]  # pour l'instant 1 seul niveau

        # Resistance = moyenne des 3 meilleurs asks
        top_asks = event.asks[:3]
        resistance = sum([price for price, qty in top_asks]) / len(top_asks)
        self.resistances = [resistance]  # pour l'instant 1 seul niveau

        await self.event_bus.publish(SupportResistanceDetected(
            supports=self.supports,
            resistances=self.resistances
        ))
        print(f"[OrderBookAnalyzer] Supports: {self.supports}, Resistances: {self.resistances}")

    async def run(self):
        # Rien à faire dans run car tout est événementiel
        pass
