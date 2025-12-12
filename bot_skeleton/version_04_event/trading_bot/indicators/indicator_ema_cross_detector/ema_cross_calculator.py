from collections import deque
import numpy as np


class IndicatorEmaCrossCalculator:
    """Détecteur de croisement EMA avec filtrage des micro-touches."""

    def __init__(self, min_gap: float = 0.01, slope_threshold: float = 0.0):
        self.min_gap = min_gap
        self.slope_threshold = slope_threshold
        self.fast_values = deque(maxlen=5)  # on garde juste 5 dernières valeurs pour le calcul
        self.slow_values = deque(maxlen=5)

    def update(self, fast_value: float, slow_value: float) -> str | None:
        self.fast_values.append(fast_value)
        self.slow_values.append(slow_value)

        if len(self.fast_values) < 2:
            return None

        # Slopes via dérivée discrete sur les 5 derniers points
        if len(self.fast_values) >= 5:
            fast_slope = np.polyfit(range(5), list(self.fast_values)[-5:], 1)[0]
            slow_slope = np.polyfit(range(5), list(self.slow_values)[-5:], 1)[0]
        else:
            fast_slope = self.fast_values[-1] - self.fast_values[-2]
            slow_slope = self.slow_values[-1] - self.slow_values[-2]

        # Différences pour croisement
        prev_diff = self.fast_values[-2] - self.slow_values[-2]
        curr_diff = self.fast_values[-1] - self.slow_values[-1]

        # Vérifier qu'il y a un cross
        if np.sign(prev_diff) == np.sign(curr_diff):
            return None

        # Filtre amplitude minimale => exprimée en unité de prix (ex: 0.0002)
        diff = fast_value - slow_value
        if abs(diff) < self.min_gap:
            return None

        # Filtre pente minimale du fast
        if abs(fast_slope) < self.slope_threshold:
            return None

        # Filtre pente cohérente entre fast et slow
        if (fast_slope > 0 > slow_slope) or (fast_slope < 0 < slow_slope):
            return None

        # Détection bullish / bearish
        if prev_diff < 0 < curr_diff and fast_slope > 0:
            return "bullish"
        if prev_diff > 0 > curr_diff and fast_slope < 0:
            return "bearish"

        return None