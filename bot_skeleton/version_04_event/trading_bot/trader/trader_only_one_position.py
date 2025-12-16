from datetime import timedelta

from trading_bot.core.logger import Logger

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeApproved, TradeClose, CandleClose

from trading_bot.trader.trade import Trade

class TraderOnlyOnePosition:
    """Exécute un seul trade à la fois avec TP/SL et envoie un événement TradeClose."""
    logger = Logger.get("TraderOnlyOnePosition")

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(TradeApproved, self.on_trade_approved)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)

        self.active_trade: Trade = None  # ✅ Une seule position à la fois
        self.last_close_timestamp = None
        self.cooldown = timedelta(minutes=3)

    async def on_trade_approved(self, event: TradeApproved):
        # Ignorer si une position est déjà ouverte
        if self.active_trade is not None:
            # print("[Trader] ⚠️ Signal ignoré : une position est déjà ouverte.")
            return

        # Ignorer si la période de cooldown n'est pas écoulée
        if self.last_close_timestamp is not None:
            elapsed = event.candle.end_time - self.last_close_timestamp
            if elapsed < self.cooldown:
                # print(f"[Trader] ⚠️ Cooldown actif ({elapsed}). Signal ignoré.")
                return
            
        self.active_trade = Trade(
            side=event.side,
            size=event.size,
            entry_price=event.candle.close,
            tp=event.tp,
            sl=event.sl,
            open_timestamp=event.candle.end_time,
            candle_open=event.candle
        )
        # self.active_trade = {
        #     "side": event.side,
        #     "entry_price": event.candle.close,
        #     "exit_price": None,
        #     "tp": event.tp,
        #     "sl": event.sl,
        #     "size": event.size,
        #     "open_timestamp": event.candle.end_time,
        #     "close_timestamp": None,
        #     "candle_open": event.candle
        # }
        self.logger.debug(f"✅ Nouvelle position ouverte : {self.active_trade}"
              f"TradeApproved={event}"
              )

    async def on_candle_close(self, event: CandleClose):

        if not self.active_trade:
            return
        
        # il faut vérifier que la bougie qui arrive est la bougie N+1 par rapport au trade ouver
        candle_open = self.active_trade.candle_open
        current_candle = event.candle
        if current_candle.is_next_of(candle_open):
            if current_candle.low <= candle_open.close <= current_candle.high:
                # si le prix de cloture de la bougie n-1 est compris dans la bougie n alors le trade est déclenché
                self.active_trade.enter_position(candle_open.close)
                # pas de rturn on peut évaluer si le trade touche tp ou sl a la bougie N+1
            else:
                # le trade actif n'est pas déclecnhé sur la bougie N+1 donc il est annuler
                self.active_trade = None
                self.last_close_timestamp = event.candle.end_time
                return

        trade = self.active_trade
        side = trade.side

        # Vérifie si TP ou SL a été touché pendant la bougie
        target = None
        if side == "BUY":
            if event.candle.high >= trade.tp:
                target = "TP"
            elif event.candle.low <= trade.sl:
                target = "SL"
        elif side == "SELL":
            if event.candle.low <= trade.tp:
                target = "TP"
            elif event.candle.high >= trade.sl:
                target = "SL"
    
        if target:

            self.active_trade.close(target, current_candle)

            await self.event_bus.publish(TradeClose(
                side=side,
                size=trade.size,
                candle_open=trade.candle_open,
                candle_close=event.candle,
                tp=trade.tp,
                sl=trade.sl,
                target=target
            ))

            self.active_trade = None
            self.last_close_timestamp = event.candle.end_time



