from trading_bot.core.logger import Logger
from trading_bot.core.events import (
    Candle,
    CandleClose,
    CandleHistoryReady,
    IndicatorUpdated,
)
from trading_bot.core.event_bus import EventBus

from trading_bot.indicators.atr_filter.atr_calculator import ATRCalculator


class IndicatorAtr:
    """
    Wrapper EventBus autour de l'ATR Wilder.
    Sert de filtre de régime de marché (accumulation / expansion).
    """

    _logger = Logger.get("IndicatorAtr")

    def __init__(
        self,
        event_bus: EventBus,
        period: int = 14,
    ):
        self.event_bus = event_bus
        self.symbol: str | None = None

        accumulation_threshold: float = 0.7
        expansion_threshold: float = 1.3
        history_multiplier: int = 3

        self.calculator = ATRCalculator(
            period=period,
            accumulation_threshold=accumulation_threshold,
            expansion_threshold=expansion_threshold,
            history_multiplier=history_multiplier,
        )

        self._initialized = False

        event_bus.subscribe(CandleHistoryReady, self.on_history_ready)
        event_bus.subscribe(CandleClose, self.on_candle_close)

        self._logger.info(
            f"period={period} "
            f"acc_th={accumulation_threshold} "
            f"exp_th={expansion_threshold}"
        )

    # ------------------------------------------------------------------
    # Historique
    # ------------------------------------------------------------------
    async def on_history_ready(self, event: CandleHistoryReady):
        self._logger.info("Initialisation ATR...")

        self.symbol = event.symbol.upper()
        candles = event.candles

        if len(candles) < self.calculator.period:
            self._logger.warning(
                f"Pas assez de données ({len(candles)}/{self.calculator.period})"
            )
            return

        value = self.calculator.initialize(candles)
        if value is None:
            return

        self._initialized = True

        await self._publish(candles[-1])

        self._logger.info(
            f"Initialisation terminée "
            f"ATR({self.calculator.period})={self.calculator.current_atr:.5f} "
            f"phase={self.calculator.market_phase()}"
        )

    # ------------------------------------------------------------------
    # Temps réel
    # ------------------------------------------------------------------
    async def on_candle_close(self, event: CandleClose):
        if not self._initialized:
            return

        if event.symbol.upper() != self.symbol:
            raise ValueError(
                f"Erreur de symbole event={event.symbol.upper()} "
                f"/ indicator={self.symbol}"
            )

        candle = event.candle
        value = self.calculator.update(candle)

        if value is None:
            return

        await self._publish(candle)

    # ------------------------------------------------------------------
    # Publication EventBus
    # ------------------------------------------------------------------
    async def _publish(self, candle: Candle):
        self._logger.debug(f"market_phase={self.calculator.market_phase()} - candle={candle}")
        await self.event_bus.publish(IndicatorUpdated(
                symbol=self.symbol,
                candle=candle,
                values={
                    "type": self.__class__.__name__,
                    "atr_value": self.calculator.current_atr,
                    "atr_period": self.calculator.period,
                    "market_phase": self.calculator.market_phase(),
                    "is_ready": self.calculator.is_ready(),
                },
            )
        )
