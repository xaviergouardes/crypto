from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import Candle, TradeSignalGenerated, IndicatorUpdated

class MaCrossFastSlowSignalEngine:

    _logger = Logger.get("MaCrossFastSlowSignalEngine")

    def __init__(self, event_bus: EventBus, periode_fast_ema: int = 9, periode_slow_ema: int = 25):
        self.event_bus = event_bus

        self.cross = None
        self.current_signal = None
        self.last_signal = None
        self.periode_slow_ema = periode_slow_ema
        self.periode_fast_ema = periode_fast_ema

        self.entry_price = None

        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)

    async def on_indicator_update(self, event: IndicatorUpdated):
        # update des donnée selemnt , la stratégie est déclacnché par le candle close
        if event.values.get("type") != "EmaCrossDetector":
            return
            
        fast_period = event.values.get("fast_period")
        slow_period = event.values.get("slow_period")
        fast_value = event.values.get("fast_value")
        slow_value = event.values.get("slow_value")

        if fast_period != self.periode_fast_ema or slow_period != self.periode_slow_ema:
            return     

        # récupérer le signal      
        self.cross = event.values.get("signal")
        if self.cross not in ("bullish", "bearish"):
            return

        signal = "BUY" if self.cross == "bullish" else "SELL"
        if self.last_signal == signal:
            return
        
        self.last_signal = signal  
        self._logger.debug(f"signal={self.last_signal} [ EMA({fast_period })={fast_value:.2f}] | EMA({slow_period})={slow_value:.2f} | candle={event.candle}")

        await self._signal_emit(event.candle)  


    async def _signal_emit(self, candle: Candle):
        await self.event_bus.publish(TradeSignalGenerated(
                    side=self.last_signal,
                    confidence=1.0,
                    candle=candle,
                    strategie=self.__class__.__name__,
                    strategie_parameters={
                        "periode_fast_ema": self.periode_fast_ema,
                        "periode_slow_ema": self.periode_slow_ema,
                    },
                    strategie_values={
                        "signal": self.last_signal,
                    },
                ))
