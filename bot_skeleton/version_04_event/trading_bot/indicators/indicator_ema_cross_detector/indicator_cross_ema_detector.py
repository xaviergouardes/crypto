

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import IndicatorUpdated
from trading_bot.indicators.indicator_ema_cross_detector.ema_cross_strategy import EmaCrossStrategy
from trading_bot.indicators.indicator_ema_cross_detector.signal_emitter import SignalEmitter
from trading_bot.indicators.indicator_ema_cross_detector.timestamphelper import TimestampHelper
from trading_bot.indicators.indicator_ema_cross_detector.value_buffer import ValueBuffer


class IndicatorEmaCrossDetector:
    """
    Traite les événements IndicatorUpdated,
    met à jour les buffers et déclenche la stratégie de croisement.
    """

    def __init__(self, event_bus: EventBus, fast_period: int, slow_period: int, buffer_size: int, slope_threshold: float = 0):
        self.event_bus = event_bus
        
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.fast_buffer = ValueBuffer(buffer_size)
        self.slow_buffer = ValueBuffer(buffer_size)
        self.strategy = EmaCrossStrategy(slope_threshold)
        self.emitter = SignalEmitter(self.event_bus)
        self.last_fast_update = None
        self.last_slow_update = None

        self.event_bus.subscribe(IndicatorUpdated, self.handle_event)

    async def handle_event(self, event: IndicatorUpdated):
        period = event.values.get("ema_candle_period")
        value = event.values.get("ema_candle")
        if period is None or value is None:
            return

        updated_fast, updated_slow = self._update_buffers(period, value, event.timestamp)
        if not (updated_fast or updated_slow):
            return

        if not self._both_ema_updated():
            return

        if not self._ema_updates_synchronized():
            return

        # Calcul des pentes via les buffers
        fast_slope = self.fast_buffer.get_slope()
        slow_slope = self.slow_buffer.get_slope()

        cross_signal = self.strategy.detect(self.fast_buffer.last_values(),
                                            self.slow_buffer.last_values(),
                                            fast_slope, slow_slope)
        if cross_signal:
             await self.emitter.emit(event.symbol, event.timestamp, cross_signal,
                                    self.fast_period, self.slow_period)

    def _update_buffers(self, period, value, timestamp):
        updated_fast = updated_slow = False
        p = int(period)

        if p == self.fast_period:
            self.fast_buffer.append(value)
            self.last_fast_update = timestamp
            updated_fast = True
        elif p == self.slow_period:
            self.slow_buffer.append(value)
            self.last_slow_update = timestamp
            updated_slow = True
        return updated_fast, updated_slow

    def _both_ema_updated(self):
        return self.last_fast_update is not None and self.last_slow_update is not None

    def _ema_updates_synchronized(self, tolerance_sec: float = 1.0):
        dt_fast = TimestampHelper.to_utc(self.last_fast_update)
        dt_slow = TimestampHelper.to_utc(self.last_slow_update)
        return abs((dt_fast - dt_slow).total_seconds()) <= tolerance_sec
    