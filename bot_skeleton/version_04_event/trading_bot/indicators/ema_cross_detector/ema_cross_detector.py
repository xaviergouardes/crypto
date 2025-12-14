from datetime import datetime, timezone
from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import Candle, IndicatorUpdated

from trading_bot.indicators.ema_cross_detector.ema_cross_calculator import IndicatorEmaCrossCalculator


class EmaCrossDetector:
    """
    Écoute IndicatorUpdated, met à jour fast/slow EMA, applique le calcul
    via IndicatorEmaCrossCalculator, et émet des signaux.
    """

    _logger = Logger.get("EmaCrossDetector")

    def __init__(self, event_bus: EventBus, fast_period: int, slow_period: int, min_gap=0.01, slope_threshold: float = 0):

        self.event_bus = event_bus

        self.fast_period = fast_period
        self.slow_period = slow_period

        self.fast_value = None
        self.slow_value = None

        self.last_fast_update = None
        self.last_slow_update = None

        # Stratégie de croisement
        self.calculator = IndicatorEmaCrossCalculator(
            min_gap=min_gap,
            slope_threshold=slope_threshold
        )

        # On écoute tous les IndicatorUpdated
        self.event_bus.subscribe(IndicatorUpdated, self.handle_indicator_updated)


    # ----------------------------------------------------------------------
    async def handle_indicator_updated(self, event: IndicatorUpdated):
        """Réception d’un indicateur EMA fast/slow → test de cross."""
        
        if event.values.get("type") != "IndicatorMovingAverage":
            return
        period = event.values.get("ema_period")
        value = event.values.get("ema_value")
        
        ts = datetime.now(timezone.utc)

        if period is None or value is None:
            return

        # ---------------------------
        # Identifier fast / slow EMA
        # ---------------------------
        if period == self.fast_period:
            self.fast_value = value
            self.last_fast_update = ts

        elif period == self.slow_period:
            self.slow_value = value
            self.last_slow_update = ts

        else:
            return  # EMA non concernée


        # Faut-il calculer ?
        if not self._both_ema_updated():
            return

        if not self._ema_updates_synchronized():
            return

        # ---------------------------
        # Application stratégie
        # ---------------------------
        signal = self.calculator.update(self.fast_value, self.slow_value)
 
        if signal:
            self._logger.debug(f"Signal détecté: {signal}")
            await self._publish(signal, event.candle)

        return

    # ------------------- Publication -------------------
    async def _publish(self, signal: int,  candle: Candle):
        await self.event_bus.publish(IndicatorUpdated(
                    symbol=candle.symbol,
                    candle=candle,
                    values={
                        "type": self.__class__.__name__,
                        "signal": signal,
                        "fast_value": self.fast_value,
                        "fast_period": self.fast_period,
                        "slow_value": self.slow_value,
                        "slow_period": self.slow_period,
                    },
                ))

    # ----------------------------------------------------------------------
    def _both_ema_updated(self):
        return self.fast_value is not None and self.slow_value is not None

    def _ema_updates_synchronized(self, tolerance_sec: float = 1.0):
        return abs((self.last_fast_update - self.last_slow_update).total_seconds()) <= tolerance_sec
