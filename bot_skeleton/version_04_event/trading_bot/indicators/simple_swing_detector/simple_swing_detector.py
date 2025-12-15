from collections import deque
from typing import Deque, Optional, List, override
from datetime import datetime
import numpy as np
import json

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated


class SimpleSwingDetector():
    """
    Détecte les swings highs/lows sur une fenêtre historique de N bougies.
    Conserve le max swing high et le min swing low dans cette fenêtre.
    """
    _logger = Logger.get("IndicatorSimpleSwingDetector")

    def __init__(self, event_bus: EventBus, swing_side: int = 2, swing_window: int = 21):
        super().__init__()
        self.event_bus = event_bus
        self.swing_side = swing_side
        self.swing_window = swing_window
        self.candles = deque(maxlen=swing_window)
        self.symbol = None

        self.max_swing_high = None
        self.min_swing_low = None
        self.prev_max = None
        self.prev_min = None

        event_bus.subscribe(CandleHistoryReady, self._on_history_ready)
        event_bus.subscribe(CandleClose, self._on_candle_close)

        self._logger.info(f"Démarré avec swing_side={self.swing_side} swing_window={self.swing_window}")


    # =====================================================
    # Initialisation avec l'historique
    # =====================================================
    async def _on_history_ready(self, event: CandleHistoryReady):
        self._logger.info(f"Initialisation ...")
        if not event.candles:
            return
        if len(event.candles) < self.candles.maxlen:
            raise Exception(f"[IndicatorSimpleSwingDetector] pas suffisament de bougie pour initilisé l'indicateur - "
                            f"swing_window={self.swing_window} > event.candles.len={len(event.candles)}")

        self.symbol = event.symbol.upper()
        for c in event.candles[-self.candles.maxlen:]:
            self.candles.append(c)
        
        self._logger.info(f"Initialisation terminée ({self.swing_window})")
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Première bougie: {self.candles[0]} ")
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSimpleSwingDetector] Dernière bougie: {self.candles[-1]}")

        await self.execute()

    # =====================================================
    # Temps réel
    # =====================================================
    async def _on_candle_close(self, event: CandleClose):
        if event.symbol.upper() != self.symbol:
            return
        
        self.candles.append(event.candle)
        await self.execute()

    # =====================================================
    # Calculs internes
    # =====================================================
    def _find_swings(self):
        """
        Identifie, dans tout l'historique self.candles, 
        le swing high le plus haut et le swing low le plus bas.
        Retourne (max_swing_high, min_swing_low).
        """
        candles = list(self.candles)
        n = self.swing_side

        swing_high = None
        swing_low = None

        # Parcours des bougies avec une marge avant/après pour analyser les swings
        for i in range(n, len(candles) - n):

            c = candles[i]
            window = candles[i - n : i + n + 1]

            # --- Swing High ---
            if c.high == max(x.high for x in window):
                if swing_high is None or c.high > swing_high.high:
                    swing_high = c

            # --- Swing Low ---
            if c.low == min(x.low for x in window):
                if swing_low is None or c.low < swing_low.low:
                    swing_low = c

        return swing_high, swing_low

    
    async def execute(self):
        
        candles = list(self.candles)

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
        window_high = max(c.high for c in candles)
        window_low = min(c.low for c in candles)

        await self.event_bus.publish(IndicatorUpdated(
                symbol=self.symbol,
                candle=self.candles[-1],
                values={
                    "type": self.__class__.__name__,
                    "last_swing_high": new_high,
                    "last_swing_low": new_low,
                    "window_high": window_high,
                    "window_low": window_low
                }
            )
        )
