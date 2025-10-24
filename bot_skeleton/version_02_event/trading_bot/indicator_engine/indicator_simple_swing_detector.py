from collections import deque
from typing import Deque, Optional, List
from datetime import datetime
import numpy as np
import json

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated


class IndicatorSimpleSwingDetector:
    """
    Détecte les swings highs/lows sur une fenêtre historique de N bougies.
    Conserve le max swing high et le min swing low dans cette fenêtre.
    """

    def __init__(self, event_bus: EventBus, lookback: int = 5, history_window: int = 100):
        self.event_bus = event_bus
        self.lookback = lookback
        self.history_window = history_window

        self.candles = deque(maxlen=history_window)
        self.symbol = None

        # Swings détectés dans la fenêtre historique
        self.swing_highs = []
        self.swing_lows = []

        self.max_swing_high = None
        self.min_swing_low = None
        self._prev_max_swing_high = None  # ← nouvelle variable pour comparer
        self._prev_min_swing_low = None   # ← nouvelle variable pour comparer
        self._initialized = False

        # Souscriptions
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] "
              f"init lookback={self.lookback} history_window={self.history_window}")


    # =====================================================
    # Initialisation avec l'historique
    # =====================================================
    async def on_history_ready(self, event: CandleHistoryReady):
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Initialisation ...")
        
        if not event.candles:
            return
        self.symbol = event.symbol.upper()
        for c in event.candles[-self.history_window:]:
            self.candles.append(c)
        self._initialized = True
        await self._compute_and_publish(event.candles[-1].end_time)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Initialisation terminée ({self.history_window})")
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Première bougie: {self.candles[0]} ")
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Dernière bougie: {self.candles[-1]}")

    # =====================================================
    # Temps réel
    # =====================================================
    async def on_candle_close(self, event: CandleClose):
        if not self._initialized or event.symbol.upper() != self.symbol:
            return
        self.candles.append(event.candle)
        await self._compute_and_publish(event.candle.end_time)

    # =====================================================
    # Calculs internes
    # =====================================================
    def _detect_swings_in_history(self):
        """
        Détecte tous les swings highs/lows dans la fenêtre historique
        et conserve la bougie qui représente chaque swing.
        """
        self.swing_highs.clear()
        self.swing_lows.clear()

        candles_list = list(self.candles)
        n = self.lookback

        for i in range(n, len(candles_list) - n):
            local_window = candles_list[i - n : i + n + 1]
            highs = [c.high for c in local_window]
            lows = [c.low for c in local_window]

            # Swing High
            if candles_list[i].high == max(highs):
                self.swing_highs.append(candles_list[i])  # stocke la bougie entière

            # Swing Low
            if candles_list[i].low == min(lows):
                self.swing_lows.append(candles_list[i])  # stocke la bougie entière

        # Mettre à jour max/min swings à partir des bougies
        if self.swing_highs:
            max_candle = max(self.swing_highs, key=lambda c: c.high)
            self.max_swing_high = max_candle

        if self.swing_lows:
            min_candle = min(self.swing_lows, key=lambda c: c.low)
            self.min_swing_low = min_candle


    async def _compute_and_publish(self, timestamp: datetime):
        self._detect_swings_in_history()

        # Ajuste les swings en fonction du dernier prix pour plus de réactivité
        last_candle = self.candles[-1]

        # Swing Low
        if self.min_swing_low and last_candle.low < self.min_swing_low.low:
            self.min_swing_low = last_candle

        # Swing High
        if self.max_swing_high and last_candle.high > self.max_swing_high.high:
            self.max_swing_high = last_candle

        # Vérifie si le max/min ont changé (en comparant prix et timestamp)
        max_changed = (
            self._prev_max_swing_high is None or
            self.max_swing_high.high != self._prev_max_swing_high.high or
            self.max_swing_high.end_time != self._prev_max_swing_high.end_time
        )

        min_changed = (
            self._prev_min_swing_low is None or
            self.min_swing_low.low != self._prev_min_swing_low.low or
            self.min_swing_low.end_time != self._prev_min_swing_low.end_time
        )

        # Publie l'event uniquement si un swing a changé
        if (self.max_swing_high is not None and self.min_swing_low is not None) and (max_changed or min_changed):
            await self.event_bus.publish(
                IndicatorUpdated(
                    symbol=self.symbol,
                    timestamp=timestamp,
                    values={
                        "type": self.__class__.__name__,
                        "max_swing_high": {
                            "price": self.max_swing_high.high,
                            "timestamp": self.max_swing_high.end_time,
                            "candle": self.max_swing_high,
                        },
                        "min_swing_low": {
                            "price": self.min_swing_low.low,
                            "timestamp": self.min_swing_low.end_time,
                            "candle": self.min_swing_low,
                        },
                    }
                )
            )
            # Met à jour les valeurs précédentes pour le prochain calcul
            self._prev_max_swing_high = self.max_swing_high
            self._prev_min_swing_low = self.min_swing_low

            # Les logs restent inchangés
            # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] "
            #     f"max_swing_high: {self.max_swing_high if self.max_swing_high else None}")
            # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] "
            #     f"min_swing_low: {self.min_swing_low if self.min_swing_low else None}")


    async def run(self):
        pass
    
