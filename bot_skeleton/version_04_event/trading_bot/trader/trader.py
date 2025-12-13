# trading_bot/trader/trader.py

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, TradeApproved, TradeClose

class Trader:
    """Simule l'exécution d'un trade approuvé avec TP et SL."""
    logger = Logger.get("Trader")
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(TradeApproved, self.on_trade_approved)
        self.active_trades = []  # trades en cours

    async def on_trade_approved(self, event: TradeApproved):
 
        self.active_trade = {
            "side": event.side,
            "entry": event.candle.close,
            "tp": event.tp,
            "sl": event.sl,
            "size": event.size,
            "open_timestamp": event.candle.end_time,
            "close_timestamp": None,
            "candle_open": event.candle
        }
        self.logger.debug(f"✅ Nouvelle position ouverte : {self.active_trade}"
              f"TradeApproved={event}"
              )

    async def on_candle_close(self, event: CandleClose):
            """Vérifie si le trade actif atteint le TP ou SL à chaque bougie close (high/low inclus)."""
            if not self.active_trade:
                return

            trade = self.active_trade
            side = trade["side"]

            # Vérifie si TP ou SL a été touché pendant la bougie
            target = None
            if side == "BUY":
                if event.candle.high >= trade["tp"]:
                    target = "TP"
                elif event.candle.low <= trade["sl"]:
                    target = "SL"
            elif side == "SELL":
                if event.candle.low <= trade["tp"]:
                    target = "TP"
                elif event.candle.high >= trade["sl"]:
                    target = "SL"
        
            if target:
                await self.event_bus.publish(TradeClose(
                    side=side,
                    size=trade["size"],
                    candle_open=trade["candle_open"],
                    candle_close=event.candle,
                    tp=trade["tp"],
                    sl=trade["sl"],
                    target=target
                ))
