import numpy as np
from collections import deque
from typing import Optional, Deque

from trading_bot.core.events import Candle


class IndicatorMovingAverageCalculator:
    """Calcule SMA ou EMA de manière indépendante, sans EventBus."""

    def __init__(self, period: int, mode: str = "EMA"):
        if mode not in ("SMA", "EMA"):
            raise ValueError("mode must be 'SMA' or 'EMA'")

        self.period = period
        self.mode = mode
        self.values: Deque[float] = deque(maxlen=period)

        self.current: Optional[float] = None
        self._sum = 0.0
        self.multiplier = 2 / (period + 1)

    def initialize(self, closes: list[float]) -> Optional[float]:
        """
        Initialise la MA à partir d'une liste brute de valeurs.
        """
        if len(closes) < self.period:
            return None

        self.values = deque(closes[-self.period:], maxlen=self.period)

        if self.mode == "SMA":
            self._sum = float(sum(self.values))
            self.current = self._sum / self.period

        else:  # EMA
            alpha = self.multiplier
            weights = (1 - alpha) ** np.arange(len(self.values) - 1, -1, -1)
            weights /= weights.sum()
            self.current = float(np.dot(self.values, weights))

        return self.current

    def update(self, close: float) -> Optional[float]:
        """
        Met à jour l’indicateur avec un nouveau close.
        """
        price = close
        # SMA
        if self.mode == "SMA":
            if len(self.values) == self.period:
                self._sum -= self.values[0]

            self.values.append(price)
            self._sum += price

            if len(self.values) < self.period:
                return None

            self.current = self._sum / self.period

        # EMA
        else:
            if self.current is None:
                # Si pas encore initialisé, construire une SMA initiale
                self.values.append(price)
                if len(self.values) == self.period:
                    self.current = sum(self.values) / self.period
                return self.current

            self.current = (price - self.current) * self.multiplier + self.current

        return self.current