from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import (
    Candle,
    IndicatorUpdated,
    CandleClose,
    TradeSignalGenerated
)

class RSICrossSignalEngine:
    """
    Détecte un croisement RSI rapide / RSI lent
    Évaluation strictement à la clôture de bougie
    """

    _logger = Logger.get("RSICrossSignalEngine")

    MIN_GAP = 0 # 1.5  seuil anti-bruit en points RSI

    def __init__(
        self,
        event_bus: EventBus,
        rsi_fast_period: int = 5,
        rsi_slow_period: int = 21,
    ):
        self.event_bus = event_bus

        self.rsi_fast_period = rsi_fast_period
        self.rsi_slow_period = rsi_slow_period

        # Symbole
        self.symbol = None

        # RSI bougie courante
        self.rsi_fast = None
        self.rsi_slow = None

        # RSI bougie précédente
        self.prev_rsi_fast = None
        self.prev_rsi_slow = None

        # Abonnements
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)

        self._logger.info(
            f"Initialisé fast={rsi_fast_period} slow={rsi_slow_period}"
        )

    # ------------------- RSI updates (intra-bougie) -------------------
    async def on_indicator_update(self, event: IndicatorUpdated):
        values = event.values
        if values.get("type") != "RSI":
            return

        candle = event.candle
        period = values.get("rsi_period")
        rsi_value = values.get("rsi_value")

        if self.symbol is None:
            self.symbol = event.symbol

        if period == self.rsi_fast_period:
            self.prev_rsi_fast = self.rsi_fast
            self.rsi_fast = (rsi_value, candle.start_time)
        elif period == self.rsi_slow_period:
            self.prev_rsi_slow = self.rsi_slow
            self.rsi_slow = (rsi_value, candle.start_time)

        # self._logger.debug(
        #     f"prev_fast={self.prev_rsi_fast} prev_slow={self.prev_rsi_slow} | "
        #     f"fast={self.rsi_fast} slow={self.rsi_slow} | "
        #     f"candle={candle}"
        # )

        if (self.prev_rsi_fast is None or self.prev_rsi_slow is None):
            # Pas assez de données pour faire la calcul
            return
        
        prev_rsi_fast, prev_rsi_fast_start = self.prev_rsi_fast
        prev_rsi_slow, prev_rsi_slow_start = self.prev_rsi_slow
        rsi_fast, rsi_fast_start = self.rsi_fast
        rsi_slow, rsi_slow_start = self.rsi_slow
        if (prev_rsi_fast_start == prev_rsi_slow_start) and (rsi_fast_start == rsi_slow_start):     

            await self.evaluate_strategy(event.values["rsi_is_oversold"] , event.values["rsi_is_overbought"], candle)

    # ------------------- Strategy -------------------
    async def evaluate_strategy(self, rsi_is_oversold, rsi_is_overbought, candle: Candle):
        if (
            self.prev_rsi_fast is None
            or self.prev_rsi_slow is None
            or self.rsi_fast is None
            or self.rsi_slow is None
        ):
            return

        prev_rsi_fast, prev_rsi_fast_start = self.prev_rsi_fast
        prev_rsi_slow, prev_rsi_slow_start = self.prev_rsi_slow
        rsi_fast, rsi_fast_start = self.rsi_fast
        rsi_slow, rsi_slow_start = self.rsi_slow

        signal = None

        # -------- Bullish cross --------
        bullish_cross = (
            prev_rsi_fast < prev_rsi_slow
            and rsi_fast > rsi_slow
            and (rsi_fast - rsi_slow) >= self.MIN_GAP
            and rsi_fast > 50
            and not rsi_is_overbought
        )

        # -------- Bearish cross --------
        bearish_cross = (
            prev_rsi_fast > prev_rsi_slow
            and rsi_fast < rsi_slow
            and (rsi_slow - rsi_fast) >= self.MIN_GAP
            and rsi_fast < 50
            and not rsi_is_oversold
        )

        if bullish_cross:
            signal = "BUY"
        elif bearish_cross:
            signal = "SELL"

        if not signal:
            return

        self._logger.debug(
            f"SIGNAL {signal} | "
            f"prev_fast={prev_rsi_fast:.2f} prev_slow={prev_rsi_slow:.2f} | "
            f"fast={rsi_fast:.2f} slow={rsi_slow:.2f} | "
            f"candle={candle}"
        )

        await self._signal_emit(signal, candle)

    # ------------------- Emit signal -------------------
    async def _signal_emit(self, signal: str, candle: Candle):
        await self.event_bus.publish(
            TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                candle=candle,
                strategie=self.__class__.__name__,
                strategie_parameters={
                    "rsi_fast_period": self.rsi_fast_period,
                    "rsi_slow_period": self.rsi_slow_period,
                    "min_gap": self.MIN_GAP,
                },
                strategie_values={
                    "rsi_fast": self.rsi_fast,
                    "rsi_slow": self.rsi_slow,
                    "prev_rsi_fast": self.prev_rsi_fast,
                    "prev_rsi_slow": self.prev_rsi_slow,
                },
            )
        )
