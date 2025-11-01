# trading_bot/risk/risk_manager.py
from datetime import datetime

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, TradeApproved, TradeRejected

class MissingPriceError(Exception):
    """Exception levée lorsqu'un TradeSignalGenerated ne contient pas de prix."""
    pass

class RiskManagerPortefolio:
    """Valide ou rejette les signaux de trading et calcule TP/SL."""

    def __init__(self, event_bus: EventBus, tp_percent: float = 1.0, sl_percent: float = 0.5, solde_inital_disponible: float = None):
        self.event_bus = event_bus

        self.max_position_size = 1.0  # taille fixe pour la simulation
        self.tp_percent = tp_percent
        self.sl_percent = sl_percent
        self.solde_disponible = solde_inital_disponible

        # S'abonner aux signaux de la stratégie
        self.event_bus.subscribe(TradeSignalGenerated, self.on_trade_signal)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [RiskManager] Initialisation terminée, riskmanager opérationnel. tp_percent={self.tp_percent} / sl_percent={self.sl_percent}")


    async def on_trade_signal(self, event: TradeSignalGenerated):
        # Vérifier la présence du prix
        if not hasattr(event, "price") or event.price is None:
            raise MissingPriceError(f"Le signal de trading ne contient pas de prix : {event}")

        if self.max_position_size <= 0:
            await self.event_bus.publish(TradeRejected(reason="Position size non autorisée"))
            print("[RiskManager] Trade rejeté : position size non autorisée")
            return

        entry_price = event.price.price

        # Calcul TP et SL selon le type de trade
        if event.side == "BUY":
            tp = entry_price * (1 + self.tp_percent / 100)
            sl = entry_price * (1 - self.sl_percent / 100)
        elif event.side == "SELL":
            tp = entry_price * (1 - self.tp_percent / 100)
            sl = entry_price * (1 + self.sl_percent / 100)
        else:
            tp = sl = None

        if self.solde_disponible is not None:
            size = self.solde_disponible / entry_price
        else:
            size = self.max_position_size

        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [RiskManager] Trade approuvé : {event.side}, taille {size}, Entry_Price {entry_price:.2f}, TP {tp:.2f}, SL {sl:.2f}")
        await self.event_bus.publish(TradeApproved(
            side=event.side,
            size=size,
            price=event.price,
            tp=tp,
            sl=sl
        ))

    async def run(self):
        pass
