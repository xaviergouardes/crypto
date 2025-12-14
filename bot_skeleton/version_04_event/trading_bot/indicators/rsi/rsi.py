from trading_bot.core.logger import Logger
from trading_bot.core.events import (
    Candle,
    CandleClose,
    CandleHistoryReady,
    IndicatorUpdated,
)
from trading_bot.core.event_bus import EventBus

from trading_bot.indicators.rsi.rsi_calculator import IndicatorRSICalculator


class RSI:
    """Wrapper EventBus autour du calculateur RSI."""

    _logger = Logger.get("RSI")

    def __init__(self, event_bus: EventBus, period: int = 14, oversold: float = 30.0, overbought: float = 70.0,):
        self.event_bus = event_bus
        self.symbol = None

        self.calculator = IndicatorRSICalculator(period, oversold, overbought)
        self._initialized = False

        event_bus.subscribe(CandleClose, self.on_candle_close)
        event_bus.subscribe(CandleHistoryReady, self.on_history_ready)

        self._logger.info(f"RSI period={period} - [{oversold}/{overbought}]")

    # ------------------- Historique -------------------
    async def on_history_ready(self, event: CandleHistoryReady):
        self._logger.info("Initialisation RSI ...")

        self.symbol = event.symbol.upper()
        candles = event.candles

        if len(candles) < self.calculator.period + 1:
            self._logger.warning(
                f"Pas assez de données ({len(candles)}/{self.calculator.period + 1})"
            )
            return

        closes = [c.close for c in candles]
        value, state = self.calculator.initialize(closes)

        self._initialized = True
        await self._publish(value, state, candles[-1])

        self._logger.info(
            f"Initialisation terminée {candles[-1]} "
            f"RSI({self.calculator.period}) = {value:.2f}"
        )

    # ------------------- Temps réel -------------------
    async def on_candle_close(self, event: CandleClose):
        if not self._initialized:
            return

        if event.symbol.upper() != self.symbol:
            raise ValueError(
                f"Erreur de symbole event={event.symbol.upper()} / indicator={self.symbol}"
            )

        candle = event.candle
        value, state = self.calculator.update(candle.close)
        self._logger.debug(f" RSI({self.calculator.period}) -> Nouvelle valeur : value={value} | state={state} | candle={candle}")

        if value is None:
            return

        await self._publish(value, state, candle)

    # ------------------- Publication -------------------
    async def _publish(self, value: float, state:str, candle: Candle):
        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                candle=candle,
                values={
                    "type": self.__class__.__name__,
                    "rsi_value": value,
                    "rsi_state": state,
                    "rsi_period": self.calculator.period,
                    "rsi_oversold": self.calculator.oversold,
                    "rsi_overbought": self.calculator.overbought,
                },
            )
        )
