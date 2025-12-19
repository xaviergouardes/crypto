from datetime import datetime
from trading_bot.core.logger import Logger
from trading_bot.core.events import Candle, CandleClose, CandleHistoryReady, IndicatorUpdated
from trading_bot.core.event_bus import EventBus

from trading_bot.indicators.moving_average.moving_average_calculator import IndicatorMovingAverageCalculator


class MovingAverage:
    """Wrapper EventBus autour du calculateur."""

    _logger = Logger.get("MovingAverage")

    def __init__(self, event_bus: EventBus, period: int = 20, mode: str = "EMA"):
        self.event_bus = event_bus

        self.symbol = None
        self.calculator = IndicatorMovingAverageCalculator(period, mode)
        self._initialized = False

        event_bus.subscribe(CandleClose, self.on_candle_close)
        event_bus.subscribe(CandleHistoryReady, self.on_history_ready)

        self._logger.info(f"mode={mode} period={period}")

    # ------------------- Historique -------------------
    async def on_history_ready(self, event: CandleHistoryReady):
        self._logger.info("Initialisation ...")

        self.symbol = event.symbol.upper()
        candles = event.candles

        if len(candles) < self.calculator.period :
            self._logger.warning(f"Pas assez de données ({len(candles)}/{self.calculator.period})")
            return
        
        closes = [c.close for c in candles]
        value = self.calculator.initialize(closes)

        self._initialized = True
        await self._publish(value, candles[-1])

        self._logger.info(
            f"Initialisation Terminée {candles[-1]} "
            f"{self.calculator.mode}({self.calculator.period}) = {value:.5f}"
        )

    # ------------------- Temps réel -------------------
    async def on_candle_close(self, event: CandleClose):
        if not self._initialized:
            return
        if event.symbol.upper() != self.symbol:
            raise ValueError(f"Erreur de symbole event={event.symbol.upper()} / indicator={self.symbol}")
        
        candle = event.candle
        value = self.calculator.update(candle.close)
        if value is None:
            return

        await self._publish(value, candle)

    # ------------------- Publication -------------------
    async def _publish(self, value: float, candle: Candle):
        self._logger.debug(f" Nouvelle Valeur EMA({self.calculator.period}) = {self.calculator.current}")
        await self.event_bus.publish(IndicatorUpdated(
                symbol=self.symbol,
                candle=candle,
                values={
                    "type": self.__class__.__name__,
                    f"{self.calculator.mode.lower()}_value": value,
                    f"{self.calculator.mode.lower()}_period": self.calculator.period,
                }
            )
        )

