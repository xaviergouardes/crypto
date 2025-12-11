from datetime import datetime, timezone

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, CandleClose, Price


class MaCrossFastSlowSignalEngine:

    _logger = Logger.get("MaCrossFastSlowSignalEngine")

    def __init__(self, event_bus: EventBus, periode_fast_ema: int = 9, periode_slow_ema: int = 25):
        self.event_bus = event_bus

        self.cross = None
        self.current_signal = None
        self.last_signal = None
        self.periode_slow_ema = periode_slow_ema
        self.periode_fast_ema = periode_fast_ema

        self.candle = None
        self.entry_price = None

        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)

    async def on_candle_close(self, event: CandleClose):
        """Chaque clôture de bougie déclenche une évaluation de la stratégie."""
        self.candle = event.candle

        now_ts = datetime.now(timezone.utc)
        self.entry_price = Price(
            symbol=self.candle.symbol,
            price=self.candle.close,  # valeur du prix
            volume=self.candle.volume,            # volume à zéro
            timestamp=self.candle.end_time     # timestamp maintenant
        )

        await self.evaluate_strategy()

    async def on_indicator_update(self, event: IndicatorUpdated):
        # update des donnée selemnt , la stratégie est déclacnché par le candle close
        if event.values.get("type") != "IndicatorEmaCrossDetector":
            return
        
        fast_period = event.values.get("fast_period")
        slow_period = event.values.get("slow_period")
        if fast_period != self.periode_fast_ema or slow_period != self.periode_slow_ema:
            return     

        # récupérer le signal      
        self.cross = event.values.get("signal")
        if self.cross not in ("bullish", "bearish"):
            return
        self._logger.debug(f"Mise à jour du signal : {self.cross}")

    async def evaluate_strategy(self):
        # Évite de répéter le même signal consécutif
        signal = "BUY" if self.cross == "bullish" else "SELL"
        if self.last_signal == signal:
            return
        
        self.last_signal = signal  
        self._logger.debug(f"Signal => {self.last_signal}")

        await self.signal_emit()  

    async def signal_emit(self):
        event = TradeSignalGenerated(
                    side=self.last_signal,
                    confidence=1.0,
                    price=self.entry_price,
                    strategie=self.__class__.__name__,
                    strategie_parameters={
                        "periode_fast_ema": self.periode_fast_ema,
                        "periode_slow_ema": self.periode_slow_ema,
                    },
                    strategie_values={
                        "cross_signal": self.cross,
                    },
                )
        await self.event_bus.publish(event)
        self._logger.debug(event)
