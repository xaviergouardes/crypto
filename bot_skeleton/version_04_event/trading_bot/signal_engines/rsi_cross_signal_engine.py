from datetime import datetime, timezone

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import (
    Candle,
    IndicatorUpdated,
    CandleClose,
    TradeSignalGenerated,
    Price,
)


class RSICrossSignalEngine:
    """
    Détecte un croisement RSI rapide / RSI lent avec filtre 50.
    """

    _logger = Logger.get("RSICrossSignalEngine")

    def __init__(
        self,
        event_bus: EventBus,
        rsi_fast_period: int = 5,
        rsi_slow_period: int = 21,
    ):
        self.event_bus = event_bus

        self.rsi_fast_period = rsi_fast_period
        self.rsi_slow_period = rsi_slow_period

        # Données courantes
        self.symbol = None
        self.candle = None

        self.rsi_fast = None
        self.rsi_slow = None

        self.prev_rsi_fast = None
        self.prev_rsi_slow = None

        # Abonnements
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)

        self._logger.info(
            f"Initialisé fast={rsi_fast_period} slow={rsi_slow_period}"
        )

    # ------------------- RSI updates -------------------
    async def on_indicator_update(self, event: IndicatorUpdated):
        values = event.values
        if values.get("type") != "IndicatorRSI":
            return

        period = values.get("rsi_period")
        rsi_value = values.get("rsi_value")

        # Initialisation du symbole
        if self.symbol is None:
            self.symbol = event.symbol

        if period == self.rsi_fast_period:
            self.prev_rsi_fast = self.rsi_fast
            self.rsi_fast = rsi_value

        elif period == self.rsi_slow_period:
            self.prev_rsi_slow = self.rsi_slow
            self.rsi_slow = rsi_value
        
        # self._logger.debug(
        #     f"Update période={period} value={rsi_value}"
        # )
            
    # ------------------- Candle close -------------------
    async def on_candle_close(self, event: CandleClose):
        if self.symbol is None:
            return

        if event.symbol.upper() != self.symbol:
            return

        self.candle = event.candle
        await self.evaluate_strategy()

    # ------------------- Strategy -------------------
    async def evaluate_strategy(self):
        if (
            self.rsi_fast is None
            or self.rsi_slow is None
            or self.prev_rsi_fast is None
            or self.prev_rsi_slow is None
        ):
            return

        signal = None

        # Croisement haussier
        bullish_cross = (
            self.prev_rsi_fast <= self.prev_rsi_slow
            and self.rsi_fast > self.rsi_slow
            and self.rsi_fast > 50
        )

        # Croisement baissier
        bearish_cross = (
            self.prev_rsi_fast >= self.prev_rsi_slow
            and self.rsi_fast < self.rsi_slow
            and self.rsi_fast < 50
        )

        if bullish_cross:
            signal = "BUY"
        elif bearish_cross:
            signal = "SELL"

        if not signal:
            return
        else:
            self._logger.debug(f"signal={signal} fast={self.rsi_fast} slow={self.rsi_slow} candle={self.candle }")
            await self._signal_emit(signal, self.candle)

    async def _signal_emit(self, signal:str, candle: Candle):
        # Création du prix
        price = Price(
            symbol=self.candle.symbol,
            price=self.candle.close,
            volume=self.candle.volume,
            timestamp=self.candle.end_time,
        )

        # Publication du signal
        await self.event_bus.publish(
            TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                price=price,
                strategie=self.__class__.__name__,
                strategie_parameters={
                    "rsi_fast_period": self.rsi_fast_period,
                    "rsi_slow_period": self.rsi_slow_period,
                },
                strategie_values={
                    "rsi_fast": self.rsi_fast,
                    "rsi_slow": self.rsi_slow,
                    "prev_rsi_fast": self.prev_rsi_fast,
                    "prev_rsi_slow": self.prev_rsi_slow,
                    "candle": self.candle,
                },
            )
        )
