import numpy as np


class EmaCrossStrategy:
    """Stratégie de détection de croisement EMA."""

    def __init__(self, slope_threshold: float = 0.0):
        self.slope_threshold = slope_threshold

    def detect(self, fast_values: list, slow_values: list, fast_slope: float, slow_slope: float) -> str | None:
        if len(fast_values) < 2 or len(slow_values) < 2:
            return None

        diff = np.array(fast_values) - np.array(slow_values)
        sign_changes = np.sign(diff[:-1]) != np.sign(diff[1:])
        if not np.any(sign_changes):
            return None

        last_change_idx = np.where(sign_changes)[0][-1]
        prev_diff = diff[last_change_idx]
        curr_diff = diff[last_change_idx + 1]

        if abs(fast_slope) < self.slope_threshold:
            return None

        if (fast_slope > 0 > slow_slope) or (fast_slope < 0 < slow_slope):
            return None

        if prev_diff < 0 < curr_diff and fast_slope > 0:
            return "bullish"
        if prev_diff > 0 > curr_diff and fast_slope < 0:
            return "bearish"

        return None