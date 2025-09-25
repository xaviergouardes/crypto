# trading_bot/risk/risk_manager.py
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, TradeApproved, TradeRejected

class MissingPriceError(Exception):
    """Exception levée lorsqu'un TradeSignalGenerated ne contient pas de prix."""
    pass

class RiskManager:
    """Valide ou rejette les signaux de trading et calcule TP/SL."""

    def __init__(self, event_bus: EventBus, tp_percent: float = 1.0, sl_percent: float = 0.5):
        self.event_bus = event_bus
        self.max_position_size = 1.0  # taille fixe pour la simulation
        self.tp_percent = tp_percent
        self.sl_percent = sl_percent

        # S'abonner aux signaux de la stratégie
        self.event_bus.subscribe(TradeSignalGenerated, self.on_trade_signal)

    async def on_trade_signal(self, event: TradeSignalGenerated):
        # Vérifier la présence du prix
        if not hasattr(event, "price") or event.price is None:
            raise MissingPriceError(f"Le signal de trading ne contient pas de prix : {event}")

        if self.max_position_size <= 0:
            await self.event_bus.publish(TradeRejected(reason="Position size non autorisée"))
            print("[RiskManager] Trade rejeté : position size non autorisée")
            return

        entry_price = event.price

        # Calcul TP et SL selon le type de trade
        if event.side == "BUY":
            tp = entry_price * (1 + self.tp_percent / 100)
            sl = entry_price * (1 - self.sl_percent / 100)
        elif event.side == "SELL":
            tp = entry_price * (1 - self.tp_percent / 100)
            sl = entry_price * (1 + self.sl_percent / 100)
        else:
            tp = sl = None

        await self.event_bus.publish(TradeApproved(
            side=event.side,
            size=self.max_position_size,
            price=entry_price,
            tp=tp,
            sl=sl
        ))
        print(f"[RiskManager] Trade approuvé : {event.side}, taille {self.max_position_size}, TP {tp:.2f}, SL {sl:.2f}")

    async def run(self):
        pass
