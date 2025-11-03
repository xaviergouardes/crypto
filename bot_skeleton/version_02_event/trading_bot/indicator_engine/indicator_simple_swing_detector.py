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

        self.max_swing_high = None
        self.min_swing_low = None
        self.prev_max = None
        self.prev_min = None

        event_bus.subscribe(CandleHistoryReady, self.on_history_ready)
        event_bus.subscribe(CandleClose, self.on_candle_close)

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
        for c in event.candles[-self.candles.maxlen:]:
            self.candles.append(c)
        
        await self._update_and_publish()

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Initialisation terminée ({self.history_window})")
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Première bougie: {self.candles[0]} ")
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Dernière bougie: {self.candles[-1]}")

    # =====================================================
    # Temps réel
    # =====================================================
    async def on_candle_close(self, event: CandleClose):
        if event.symbol.upper() != self.symbol:
            return
        
        self.candles.append(event.candle)
        await self._update_and_publish()

    # =====================================================
    # Calculs internes
    # =====================================================
    def _find_swings(self):
        """Retourne (max_swing_high, min_swing_low)"""
        candles = list(self.candles)
        n = self.lookback

        swing_high = None
        swing_low = None

        for i in range(n, len(candles) - n):
            window = candles[i-n:i+n+1]

            if candles[i].high == max(c.high for c in window):
                if swing_high is None or candles[i].high > swing_high.high:
                    swing_high = candles[i]

            if candles[i].low == min(c.low for c in window):
                if swing_low is None or candles[i].low < swing_low.low:
                    swing_low = candles[i]

        return swing_high, swing_low
    

    async def _update_and_publish(self):
        new_high, new_low = self._find_swings()

        # Si on ne trouve rien, on ne publie rien
        if new_high is None or new_low is None:
            return

        # Si rien n'a changé, on arrête
        if new_high == self.prev_max and new_low == self.prev_min:
            return

        # MàJ
        self.prev_max = self.max_swing_high = new_high
        self.prev_min = self.min_swing_low = new_low

        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] | "
        #       f"current candle={self.candles[-1]} | Upadted -> "
        #       f"swing high={self.max_swing_high} | swing low={self.min_swing_low} "
        #       )

        # compute highest/lowest of history window
        window_high = max(c.high for c in self.candles)
        window_low = min(c.low for c in self.candles)

        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                timestamp=datetime.utcnow(),
                values={
                    "type": self.__class__.__name__,
                    "last_swing_high": new_high,
                    "last_swing_low": new_low,
                    "window_high": window_high,
                    "window_low": window_low
                }
            )
        )


    async def run(self):
        pass