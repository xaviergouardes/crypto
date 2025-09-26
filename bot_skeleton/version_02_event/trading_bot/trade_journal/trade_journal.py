# trading_bot/trader/trader.py
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose

class TradeJournal:
    """Simule l'exécution d'un trade approuvé avec TP et SL."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(TradeClose, self.on_trade_close)

    async def on_trade_close(self, event: TradeClose):
        pnl = None
        if event["side"] == "BUY":
            if event["target"] == "TP":
                pnl = event["tp"] - event["price"]
            elif event["target"] == "SL":
                pnl = - ( event["price"] - event["sl"] )

        elif trade["side"] == "SELL":
            if price <= trade["tp"]:
                pnl = event["price"] - event["tp"]
            elif event["target"] == "SL":
                pnl = - ( event["sl"] - event["price"] )

        print(f"[Trader] Trade ouvert : {event} => P&N = {pnl*size}")

    async def run(self):
        # Tout est événementiel, rien à faire ici
        pass
