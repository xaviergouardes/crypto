from datetime import datetime, timezone

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, CandleClose, Price


class RandomSignalEngine:
    """
    Stratégie Sweep Swing compatible avec IndicatorSimpleSwingDetector :
    """
    logger = Logger.get("RandomSignalEngine")

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.entry_price = None

        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.logger.info("[RandomSignalEngine] Initisé") 

    async def on_candle_close(self, event: CandleClose):
        """Chaque clôture de bougie déclenche une évaluation de la stratégie."""
        candle = event.candle

        minute = candle.start_time.minute
        if minute % 2 == 0:
            signal = "BUY"
        else:
            signal = "SELL"

        # Log clair
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [RandomSignalEngine] "
        #       f"Signal {signal} | candle={candle} "
        # )

        now_ts = datetime.now(timezone.utc)
        price = Price(
            symbol=event.symbol,
            price=candle.close,  # valeur du prix
            volume=0,            # volume à zéro
            timestamp=now_ts     # timestamp maintenant
        )

        # Publication du signal
        await self.event_bus.publish(TradeSignalGenerated(
            side=signal,
            confidence=1.0,
            price=price,
            strategie = self.__class__.__name__,
            strategie_parameters = None,
            strategie_values = None,
        ))


 
