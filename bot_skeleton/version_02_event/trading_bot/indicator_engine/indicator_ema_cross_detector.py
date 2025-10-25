from collections import deque
from datetime import datetime
import numpy as np
from zoneinfo import ZoneInfo

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import IndicatorUpdated


class IndicatorEmaCrossDetector:
    """
    Détecte les croisements entre une EMA rapide et une EMA lente.

    - Écoute les événements `IndicatorUpdated`
    - Stocke les dernières valeurs de chaque EMA dans des buffers
    - Ne déclenche le calcul du croisement que lorsqu’on a reçu une nouvelle EMA fast ET une nouvelle EMA slow
    """

    def __init__(self, event_bus: EventBus, fast_period: int, slow_period: int, buffer_size: int = 2, slope_threshold: float = 0):
        self.event_bus = event_bus

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.buffer_size = buffer_size
        self.slope_threshold = slope_threshold

        # Buffers pour lisser les détections
        self.fast_values = deque(maxlen=buffer_size)
        self.slow_values = deque(maxlen=buffer_size)

        # Timestamps des dernières MAJ reçues (pour détecter si les deux EMA ont été mises à jour)
        self.last_fast_update = None
        self.last_slow_update = None

        # Inscription à l’EventBus
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_updated)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorEmaCrossDetector] "
              f"fast_period={self.fast_period} slow_period={self.slow_period} / "
              f"buffer_size={self.buffer_size} slope_threshold={self.slope_threshold}"

              )


    async def on_indicator_updated(self, event: IndicatorUpdated):
        """
        Traite chaque mise à jour d'un indicateur.
        On s'intéresse uniquement aux EMA fast et slow.
        """
        period = event.values.get("ema_candle_period")
        value = event.values.get("ema_candle")
        if period is None or value is None:
            return

        updated_fast = False
        updated_slow = False

        # Mise à jour du buffer correspondant
        if int(period) == self.fast_period:
            self.fast_values.append(float(value))
            self.last_fast_update = event.timestamp
            updated_fast = True

        elif int(period) == self.slow_period:
            self.slow_values.append(float(value))
            self.last_slow_update = event.timestamp
            updated_slow = True

        # ✅ Calcul uniquement si on a reçu une MAJ de fast ET de slow depuis la dernière analyse
        if not (updated_fast or updated_slow):
            return

        # Vérifie que les deux EMA ont bien été mises à jour au moins une fois
        if self.last_fast_update is None or self.last_slow_update is None:
            return

        # Si les timestamps sont identiques ou très proches, on considère que les deux EMA sont à jour
        if abs((self._to_datetime(self.last_fast_update) - self._to_datetime(self.last_slow_update)).total_seconds()) <= 1:
            cross = self.is_crossing(self.slope_threshold)
            if cross:
                paris_tz = ZoneInfo("Europe/Paris")
                event_time_str = self._to_datetime(event.timestamp).astimezone(paris_tz).strftime("%Y-%m-%d %H:%M:%S")

                # print(
                #     f"{datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')} "
                #     f"[IndicatorEmaCrossDetector] 🔔 Croisement détecté : {cross.upper()} "
                #     f"(time={event_time_str} / fast_period={self.fast_period} / slow_period={self.slow_period})"
                # )

                # Émettre un nouvel événement si besoin
                await self.event_bus.publish(
                    IndicatorUpdated(
                        symbol=event.symbol,
                        timestamp=event.timestamp,
                        values={
                            "type": self.__class__.__name__,
                            "signal": cross,
                            "fast_period": self.fast_period,
                            "slow_period": self.slow_period,
                        },
                    )
                )

    def is_crossing(self, slope_threshold: float = 0.0):
        """Détecte un croisement EMA rapide / EMA lente en utilisant toutes les valeurs du buffer."""
        if not self.is_ready():
            return None

        fast = np.array(self.fast_values, dtype=float)
        slow = np.array(self.slow_values, dtype=float)
        diff = fast - slow

        sign_changes = np.sign(diff[:-1]) != np.sign(diff[1:])
        if not np.any(sign_changes):
            return None

        last_change_idx = np.where(sign_changes)[0][-1]
        prev_diff = diff[last_change_idx]
        curr_diff = diff[last_change_idx + 1]

        fast_slope = self.get_slope(self.fast_values)
        slow_slope = self.get_slope(self.slow_values)

        if abs(fast_slope) < slope_threshold:
            return None

        if (fast_slope > 0 and slow_slope < 0) or (fast_slope < 0 and slow_slope > 0):
            return None

        if prev_diff < 0 and curr_diff > 0 and fast_slope > 0:
            return "bullish"
        elif prev_diff > 0 and curr_diff < 0 and fast_slope < 0:
            return "bearish"
        return None

    def is_ready(self) -> bool:
        """Vérifie si les deux buffers sont remplis."""
        return (len(self.fast_values) == self.buffer_size) and (len(self.slow_values) == self.buffer_size)

    def get_slope(self, values: deque) -> float:
        """Calcule la pente moyenne via une régression linéaire."""
        n = len(values)
        if n < 2:
            return 0.0
        x = np.arange(n)
        y = np.array(values, dtype=float)
        slope, _ = np.polyfit(x, y, 1)
        return slope

    def _to_datetime(self, ts):
        """Convertit un timestamp (datetime ou str ISO) en datetime UTC."""
        if isinstance(ts, datetime):
            return ts if ts.tzinfo else ts.replace(tzinfo=ZoneInfo("UTC"))
        return datetime.fromisoformat(str(ts)).replace(tzinfo=ZoneInfo("UTC"))

    async def run(self):
        # Tout est événementiel
        pass
