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
        self._update_current_swings()

        if self._swings_changed():
            await self._publish_swings(timestamp)
            self._remember_current_swings()
    
    def _update_current_swings(self):
        self.max_swing_high = self.swing_highs[-1] if self.swing_highs else None
        self.min_swing_low = self.swing_lows[-1] if self.swing_lows else None

    def _swings_changed(self):
        # Si avant il n'y en avait pas et maintenant oui
        if self.max_swing_high is None or self.min_swing_low is None:
            return not (self._prev_max_swing_high is None and self._prev_min_swing_low is None)

        # Si on passe de None à quelque chose ou inverse
        if self._prev_max_swing_high is None or self._prev_min_swing_low is None:
            return True
        
        return (
            self.max_swing_high.end_time != self._prev_max_swing_high.end_time
            or self.min_swing_low.end_time != self._prev_min_swing_low.end_time
        )
    
    def _remember_current_swings(self):
        self._prev_max_swing_high = self.max_swing_high
        self._prev_min_swing_low = self.min_swing_low


    async def _publish_swings(self, timestamp: datetime):
        if self.max_swing_high is None or self.min_swing_low is None:
            return
        
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] | "
        #       f"current candle={self.candles[-1]} | "
        #       f"swing high={self.max_swing_high} | swing low={self.min_swing_low} "
        #       )
  
        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                timestamp=timestamp,
                values={
                    "type": self.__class__.__name__,
                    "max_swing_high": {
                        "price": self.max_swing_high.high,
                        "timestamp": self.max_swing_high.end_time,
                    },
                    "min_swing_low": {
                        "price": self.min_swing_low.low,
                        "timestamp": self.min_swing_low.end_time,
                    },
                }
            )
        )


    async def run(self):
        pass