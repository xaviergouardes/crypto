# trading_bot/risk/risk_manager.py
from datetime import datetime

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import (
    TradeSignalGenerated,
    TradeApproved,
    NewSoldes,
    IndicatorUpdated,
)


class MissingPriceError(Exception):
    """Exception levée lorsqu'un TradeSignalGenerated ne contient pas de prix."""
    pass


class RiskManagerByAtr:
    """Gère le risque et calcule TP/SL dynamiquement à partir de l’ATR."""

    def __init__(self, event_bus: EventBus, atr_tp_mult: float = 2.0, atr_sl_mult: float = 1.0, solde_disponible: float = None):
        self.event_bus = event_bus
        self.max_position_size = 1.0
        self.solde_disponible = solde_disponible

        # Multiplicateurs ATR
        self.atr_tp_mult = atr_tp_mult
        self.atr_sl_mult = atr_sl_mult

        # Dernière valeur ATR connue
        self.current_atr = None

        # Abonnement aux événements
        self.event_bus.subscribe(TradeSignalGenerated, self.on_trade_signal)
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_updated)
        self.event_bus.subscribe(NewSoldes, self.on_new_soldes)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [RiskManager] Initialisé avec ATR multipliers : TP={atr_tp_mult}x / SL={atr_sl_mult}x")

    async def on_new_soldes(self, event: NewSoldes):
        self.solde_disponible = event.usdc

    async def on_indicator_updated(self, event: IndicatorUpdated):
        """Met à jour la valeur de l’ATR quand elle change."""
        # ATR
        if "atr" in event.values:
            self.current_atr = event.values["atr"]

    async def on_trade_signal(self, event: TradeSignalGenerated):
        """Calcule TP/SL dynamiquement à partir de l’ATR."""
        if not hasattr(event, "price") or event.price is None:
            raise MissingPriceError(f"Le signal ne contient pas de prix : {event}")

        if self.current_atr is None:
            print("[RiskManager] ⚠️ ATR non disponible — trade ignoré.")
            return

        entry_price = event.price.price

        if event.side == "BUY":
            tp = entry_price + (self.current_atr * self.atr_tp_mult)
            sl = entry_price - (self.current_atr * self.atr_sl_mult)
        elif event.side == "SELL":
            tp = entry_price - (self.current_atr * self.atr_tp_mult)
            sl = entry_price + (self.current_atr * self.atr_sl_mult)
        else:
            # print(f"[RiskManager] ⚠️ Type de trade inconnu : {event.side}")
            return

        if self.solde_disponible is not None:
            size = self.solde_disponible / entry_price
        else:
            size = self.max_position_size

        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [RiskManager] Trade approuvé avec ATR / TradeSignalGenerated={event}")
        # print(f"  ➤ {event.side} | Entry: {entry_price:.5f} | TP: {tp:.5f} | SL: {sl:.5f}")

        await self.event_bus.publish(TradeApproved(
            side=event.side,
            size=size,
            price=event.price,
            tp=tp,
            sl=sl
        ))


    async def run(self):
        pass
