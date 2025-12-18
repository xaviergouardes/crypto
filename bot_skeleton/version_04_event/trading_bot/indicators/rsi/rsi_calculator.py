from typing import Optional
from collections import deque
import numpy as np

from enum import Enum

class RSIState(str, Enum):
    OVERSOLD = "oversold"
    OVERBOUGHT = "overbought"
    NEUTRAL = "neutral"

class IndicatorRSICalculator:
    """
    Calcule RSI (Wilder) + état logique.
    """

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

        self.prev_close: Optional[float] = None
        self.avg_gain: Optional[float] = None
        self.avg_loss: Optional[float] = None

        self.current: Optional[float] = None
        self.state: Optional[RSIState] = None

        self.gains = deque(maxlen=period)
        self.losses = deque(maxlen=period)

    # ------------------- Initialisation -------------------
    def initialize(self, closes: list[float]) -> Optional[float]:
        if len(closes) < self.period + 1:
            return None

        gains, losses = [], []

        for i in range(-self.period, 0):
            delta = closes[i] - closes[i - 1]
            gains.append(max(delta, 0.0))
            losses.append(max(-delta, 0.0))

        self.avg_gain = float(np.mean(gains))
        self.avg_loss = float(np.mean(losses))
        self.prev_close = closes[-1]

        self.current = self._compute_rsi()
        self.state = self._compute_state(self.current)
        return self.current, self.state

    # ------------------- Update -------------------
    def update(self, close: float) -> Optional[float]:
        if self.prev_close is None:
            self.prev_close = close
            return None

        delta = close - self.prev_close
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)

        if self.avg_gain is None or self.avg_loss is None:
            self.gains.append(gain)
            self.losses.append(loss)

            if len(self.gains) < self.period:
                self.prev_close = close
                return None

            self.avg_gain = sum(self.gains) / self.period
            self.avg_loss = sum(self.losses) / self.period
        else:
            self.avg_gain = (self.avg_gain * (self.period - 1) + gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + loss) / self.period

        self.prev_close = close

        self.current = self._compute_rsi()
        self.state = self._compute_state(self.current)
        return self.current, self.state

    # ------------------- RSI -------------------
    def _compute_rsi(self) -> float:
        if self.avg_loss == 0:
            return 100.0
        rs = self.avg_gain / self.avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    # ------------------- State -------------------
    def _compute_state(self, rsi: float) -> str:
        if rsi <= self.oversold:
            return RSIState.OVERSOLD
        if rsi >= self.overbought:
            return RSIState.OVERBOUGHT
        return "NEUTRAL"

    def is_oversold(self) -> bool:
        return self.state is RSIState.OVERSOLD

    def is_overbought(self) -> bool:
        return self.state is RSIState.OVERBOUGHT

    def is_neutral(self) -> bool:
        return self.state is RSIState.NEUTRAL
