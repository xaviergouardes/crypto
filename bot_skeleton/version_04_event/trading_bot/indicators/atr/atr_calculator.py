import numpy as np
from collections import deque
from typing import Optional, Deque

from trading_bot.core.events import Candle


class ATRCalculator:
    """
    ATR Wilder exact (J. Welles Wilder)
    + Détection de phase de marché (accumulation / expansion)
    """

    def __init__(
        self,
        period: int = 14,
        accumulation_threshold: float = 0.7,
        expansion_threshold: float = 1.3,
        history_multiplier: int = 3,
    ):
        self.period = period
        self.accumulation_threshold = accumulation_threshold
        self.expansion_threshold = expansion_threshold
        self.history_multiplier = history_multiplier

        # Fenêtre de calcul ATR
        self.tr_values: Deque[float] = deque(maxlen=period)

        # Historique ATR pour régime de marché
        self.atr_values: Deque[float] = deque(
            maxlen=period * history_multiplier
        )

        self.previous_close: Optional[float] = None
        self.current_atr: Optional[float] = None

    # ------------------------------------------------------------------
    # True Range
    # ------------------------------------------------------------------
    def compute_true_range(
        self,
        high: float,
        low: float,
        close: float
    ) -> float:
        if self.previous_close is None:
            tr = high - low
        else:
            tr = max(
                high - low,
                abs(high - self.previous_close),
                abs(low - self.previous_close)
            )
        self.previous_close = close
        return tr

    # ------------------------------------------------------------------
    # Bootstrap (3 × period)
    # ------------------------------------------------------------------
    def initialize(self, candles: list[Candle]) -> Optional[float]:
        """
        Initialise complètement l'ATR Wilder.
        Nécessite >= period bougies.
        Optimal : >= history_multiplier × period.
        """
        if len(candles) < self.period:
            return None

        candles = candles[-self.period * self.history_multiplier :]

        self.tr_values.clear()
        self.atr_values.clear()
        self.previous_close = None
        self.current_atr = None

        tr_list: list[float] = []

        # 1️⃣ Calcul des True Range
        for candle in candles:
            tr = self.compute_true_range(
                candle.high,
                candle.low,
                candle.close
            )
            tr_list.append(tr)

        # 2️⃣ Premier ATR = SMA(period)
        if len(tr_list) < self.period:
            return None

        first_atr = float(np.mean(tr_list[: self.period]))
        self.current_atr = first_atr
        self.atr_values.append(first_atr)

        # 3️⃣ Wilder smoothing
        for tr in tr_list[self.period :]:
            self.current_atr = (
                (self.current_atr * (self.period - 1)) + tr
            ) / self.period
            self.atr_values.append(self.current_atr)

        # 4️⃣ Fenêtre TR prête pour update live
        self.tr_values = deque(
            tr_list[-self.period :],
            maxlen=self.period
        )

        return self.current_atr

    # ------------------------------------------------------------------
    # Update live
    # ------------------------------------------------------------------
    def update(self, candle: Candle) -> Optional[float]:
        """
        Met à jour l'ATR avec une nouvelle bougie (Wilder exact).
        """
        tr = self.compute_true_range(
            candle.high,
            candle.low,
            candle.close
        )

        # Phase de construction initiale
        if self.current_atr is None:
            self.tr_values.append(tr)
            if len(self.tr_values) < self.period:
                return None

            self.current_atr = float(np.mean(self.tr_values))
            self.atr_values.append(self.current_atr)
            return self.current_atr

        # Wilder smoothing
        self.current_atr = (
            (self.current_atr * (self.period - 1)) + tr
        ) / self.period

        self.tr_values.append(tr)
        self.atr_values.append(self.current_atr)

        return self.current_atr

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def is_ready(self) -> bool:
        return len(self.atr_values) >= self.period * 2

    def market_phase(self) -> str:
        """
        Retourne la phase du marché :
        - accumulation
        - expansion
        - neutral
        """
        if not self.is_ready():
            return "neutral"

        avg_atr = float(np.mean(self.atr_values))
        ratio = self.current_atr / avg_atr if avg_atr > 0 else 0.0

        if ratio < self.accumulation_threshold:
            return "accumulation"
        elif ratio > self.expansion_threshold:
            return "expansion"
        else:
            return "neutral"
