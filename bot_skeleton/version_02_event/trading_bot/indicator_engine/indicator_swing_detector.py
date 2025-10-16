from collections import deque
from typing import Deque, Optional, List
from datetime import datetime

import numpy as np
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated


class IndicatorSwingDetector:
    """
    Indicateur de détection de Swing High / Swing Low.
    Inspiré des concepts ICT et de la logique d'une salle de marché.

    Paramètres :
        - event_bus : EventBus
        - lookback : profondeur de détection (nb de bougies avant/après)
        - min_distance : nombre minimum de bougies entre deux swings
        - min_strength : rapport minimal d'amplitude (swing significatif)
    """
    """
    | Paramètre      | Ce qu’il contrôle                  | Effet d’une valeur basse    | Effet d’une valeur haute         |
    | -------------- | ---------------------------------- | --------------------------- | -------------------------------- |
    | `lookback`     | largeur de la fenêtre de détection | plus réactif, plus de bruit | plus lent, plus fiable           |
    | `min_distance` | espacement entre swings            | swings fréquents            | swings espacés                   |
    | `min_strength` | filtrage par amplitude/volatilité  | plus de petits swings       | garde seulement les swings forts |
    """

    def __init__(self, event_bus: EventBus, lookback: int = 3, min_distance: int = 5, min_strength: float = 1.2):
        self.event_bus = event_bus
        self.lookback = lookback
        self.min_distance = min_distance
        self.min_strength = min_strength

        # Données
        self.candles: Deque = deque(maxlen=5000)
        self.symbol: Optional[str] = None
        self._initialized = False

        # Résultats
        self.last_swing_high: Optional[float] = None
        self.last_swing_low: Optional[float] = None
        self.last_swing_type: Optional[str] = None
        self.current_swings: List[dict] = []

        # Souscriptions
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSwingDetector] "
              f"init lookback={self.lookback} min_distance={self.min_distance}")

    # -----------------------------------------------------
    # Historique initial
    # -----------------------------------------------------
    async def on_history_ready(self, event: CandleHistoryReady):
        """Initialise les bougies à partir de l'historique reçu."""
        if not event.candles:
            return

        self.symbol = event.symbol.upper()
        for candle in event.candles:
            self.candles.append(candle)

        self._initialized = True
        await self._compute_and_publish(event.candles[-1].end_time)

    # -----------------------------------------------------
    # Temps réel
    # -----------------------------------------------------
    async def on_candle_close(self, event: CandleClose):
        """Ajoute la bougie et met à jour les swings."""
        if not self._initialized or event.symbol.upper() != self.symbol:
            return

        self.candles.append(event.candle)
        await self._compute_and_publish(event.candle.end_time)

    # -----------------------------------------------------
    # Calculs internes
    # -----------------------------------------------------
    async def _compute_and_publish(self, timestamp: datetime):
        """Détecte les swings pertinents et publie le dernier état."""
        highs = np.array([c.high for c in self.candles])
        lows = np.array([c.low for c in self.candles])

        swing_highs, swing_lows = self._detect_swings(highs, lows)
        swings = []

        for i in swing_highs:
            swing = {
                "index": i,
                "price": highs[i],
                "type": "high",
                "strength": self._compute_strength(i, highs, lows, kind="high"),
                "timestamp": self.candles[i].end_time,
            }
            if swing["strength"] >= self.min_strength:
                swings.append(swing)

        for i in swing_lows:
            swing = {
                "index": i,
                "price": lows[i],
                "type": "low",
                "strength": self._compute_strength(i, highs, lows, kind="low"),
                "timestamp": self.candles[i].end_time,
            }
            if swing["strength"] >= self.min_strength:
                swings.append(swing)

        # Tri par timestamp et mise à jour des swings récents
        swings = sorted(swings, key=lambda x: x["timestamp"])
        if swings:
            self.current_swings = swings[-10:]  # garder les 10 derniers
            last = swings[-1]
            self.last_swing_type = last["type"]
            if last["type"] == "high":
                self.last_swing_high = last["price"]
            else:
                self.last_swing_low = last["price"]

        await self._publish(timestamp)

    def _detect_swings(self, highs, lows):
        """Renvoie les index de swing highs et lows."""
        n = self.lookback
        swing_highs, swing_lows = [], []

        for i in range(n, len(highs) - n):
            if highs[i] == max(highs[i - n:i + n + 1]):
                if not swing_highs or (i - swing_highs[-1]) >= self.min_distance:
                    swing_highs.append(i)
            if lows[i] == min(lows[i - n:i + n + 1]):
                if not swing_lows or (i - swing_lows[-1]) >= self.min_distance:
                    swing_lows.append(i)
        return swing_highs, swing_lows

    def _compute_strength(self, i, highs, lows, kind="high"):
        """Calcule la force relative du swing."""
        n = self.lookback
        start = max(0, i - n)
        end = min(len(highs), i + n)
        atr = np.mean(highs[start:end] - lows[start:end])
        if atr == 0:
            return 0.0

        if kind == "high":
            amplitude = highs[i] - np.min(lows[start:end])
        else:
            amplitude = np.max(highs[start:end]) - lows[i]
        return amplitude / atr

    # -----------------------------------------------------
    # Publication
    # -----------------------------------------------------
    async def _publish(self, timestamp: datetime):
        """Publie l'événement IndicatorUpdated avec les swings récents."""
        if not self.symbol:
            return

        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                timestamp=timestamp,
                values={
                    "last_swing_high": self.last_swing_high,
                    "last_swing_low": self.last_swing_low,
                    "last_swing_type": self.last_swing_type,
                    "swings": self.current_swings,
                    "lookback": self.lookback,
                    "min_distance": self.min_distance,
                }
            )
        )

    async def run(self):
        # Mode événementiel — pas de boucle
        pass
