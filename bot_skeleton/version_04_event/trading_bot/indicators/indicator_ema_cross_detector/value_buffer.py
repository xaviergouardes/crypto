from collections import deque

import numpy as np


class ValueBuffer:
    """Stocke les dernières valeurs et calcule des métriques comme la pente."""

    def __init__(self, size: int):
        self.values = deque(maxlen=size)

    def append(self, value: float):
        self.values.append(float(value))

    def is_full(self):
        return len(self.values) == self.values.maxlen

    def get_slope(self) -> float:
        n = len(self.values)
        if n < 2:
            return 0.0
        x = np.arange(n)
        y = np.array(self.values, dtype=float)
        slope, _ = np.polyfit(x, y, 1)
        return slope

    def last_values(self):
        return list(self.values)
