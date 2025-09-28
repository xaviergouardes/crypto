# trading_bot/trader/trader.py
from datetime import datetime

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeApproved, PriceUpdated, TradeClose

class TraderOnlyOnePosition:
    """Exécute un seul trade à la fois avec TP/SL et envoie un événement TradeClose."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(TradeApproved, self.on_trade_approved)
        self.event_bus.subscribe(PriceUpdated, self.on_price)
        self.active_trade = None  # ✅ Une seule position à la fois

    async def on_trade_approved(self, event: TradeApproved):
        # Ignorer si une position est déjà ouverte
        if self.active_trade is not None:
            # print("[Trader] ⚠️ Signal ignoré : une position est déjà ouverte.")
            return

        self.active_trade = {
            "side": event.side,
            "entry": event.price,
            "tp": event.tp,
            "sl": event.sl,
            "size": event.size,
            "open_timestamp": datetime.utcnow(),
            "close_timestamp": None
        }
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Trader] ✅ Nouvelle position ouverte : {self.active_trade}")

    async def on_price(self, event: PriceUpdated):
        if self.active_trade is None:
            return  # Aucun trade en cours

        trade = self.active_trade
        price = event.price
        closed = False
        target = None

        if trade["side"] == "BUY":
            if price >= trade["tp"]:
                target = "TP"
                closed = True
                # print(f"[Trader] ✅ TP atteint ! Clôture BUY à {price:.2f}")
            elif price <= trade["sl"]:
                target = "SL"
                closed = True
                # print(f"[Trader] 🛑 SL atteint ! Clôture BUY à {price:.2f}")

        elif trade["side"] == "SELL":
            if price <= trade["tp"]:
                target = "TP"
                closed = True
                # print(f"[Trader] ✅ TP atteint ! Clôture SELL à {price:.2f}")
            elif price >= trade["sl"]:
                target = "SL"
                closed = True
                # print(f"[Trader] 🛑 SL atteint ! Clôture SELL à {price:.2f}")

        # Si le trade est clôturé, on publie l'événement et on réinitialise l'état
        if closed:
            await self.event_bus.publish(TradeClose(
                side=trade["side"],
                price=trade["entry"],
                tp=trade["tp"],
                sl=trade["sl"],
                size=trade["size"],
                target=target,
                open_timestamp=trade["open_timestamp"],
                close_timestamp=datetime.utcnow()
            ))
            self.active_trade = None  # ✅ prêt pour un nouveau trade

    async def run(self):
        # Tout est événementiel, rien à faire ici
        pass

