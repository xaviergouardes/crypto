# trading_bot/trader/trader.py
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeApproved, PriceUpdated

class Trader:
    """Simule l'exécution d'un trade approuvé avec TP et SL."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(TradeApproved, self.on_trade_approved)
        self.event_bus.subscribe(PriceUpdated, self.on_price)
        self.active_trades = []  # trades en cours

    async def on_trade_approved(self, event: TradeApproved):
        trade = {
            "side": event.side,
            "entry": event.price,
            "tp": event.tp,
            "sl": event.sl,
            "size": event.size
        }
        self.active_trades.append(trade)
        print(f"[Trader] Trade ouvert : {trade}")

    async def on_price(self, event: PriceUpdated):
        to_close = []
        for trade in self.active_trades:
            price = event.price
            if trade["side"] == "BUY":
                if price >= trade["tp"]:
                    print(f"[Trader] TP atteint ! Clôture trade BUY à {price:.2f}")
                    to_close.append(trade)
                elif price <= trade["sl"]:
                    print(f"[Trader] SL atteint ! Clôture trade BUY à {price:.2f}")
                    to_close.append(trade)
            elif trade["side"] == "SELL":
                if price <= trade["tp"]:
                    print(f"[Trader] TP atteint ! Clôture trade SELL à {price:.2f}")
                    to_close.append(trade)
                elif price >= trade["sl"]:
                    print(f"[Trader] SL atteint ! Clôture trade SELL à {price:.2f}")
                    to_close.append(trade)

        for trade in to_close:
            self.active_trades.remove(trade)

    async def run(self):
        # Tout est événementiel, rien à faire ici
        pass
