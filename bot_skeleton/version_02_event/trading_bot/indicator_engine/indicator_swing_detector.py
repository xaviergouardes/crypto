from collections import deque
from typing import Deque, Optional, List
from datetime import datetime
import numpy as np
import json

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated


class IndicatorSwingDetector:
    """
    Indicateur de détection de Swing High / Swing Low (ICT-style amélioré).

    Objectif : détecter les swings forts, significatifs, et structurels.

    Paramètres :
        - lookback : nb de bougies avant/après à comparer pour un swing
        - min_distance : espacement minimal entre deux swings du même type
        - min_strength : score minimum pour considérer un swing comme fort

    Le score global combine :
        - force d’amplitude (60 %)
        - dominance structurelle (20 %)
        - rejet de bougie (20 %)
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
        self.strong_swings: List[dict] = []

        # Souscriptions
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSwingDetector] "
              f"init lookback={self.lookback} min_distance={self.min_distance}")

    # =====================================================
    # Initialisation avec l'historique
    # =====================================================
    async def on_history_ready(self, event: CandleHistoryReady):
        """Initialise les bougies à partir de l'historique reçu."""
        if not event.candles:
            return

        self.symbol = event.symbol.upper()
        for candle in event.candles:
            self.candles.append(candle)

        self._initialized = True
        await self._compute_and_publish(event.candles[-1].end_time)

    # =====================================================
    # Temps réel
    # =====================================================
    async def on_candle_close(self, event: CandleClose):
        """Ajoute la bougie et met à jour les swings."""
        if not self._initialized or event.symbol.upper() != self.symbol:
            return

        self.candles.append(event.candle)
        await self._compute_and_publish(event.candle.end_time)

    # =====================================================
    # Calculs internes
    # =====================================================
    async def _compute_and_publish(self, timestamp: datetime):
        """Détecte les swings forts et publie l’état."""
        highs = np.array([c.high for c in self.candles])
        lows = np.array([c.low for c in self.candles])

        swing_highs, swing_lows = self._detect_swings(highs, lows)
        swings = []

        for i in swing_highs:
            score = self._compute_swing_score(i, highs, lows, kind="high", swings=swings)
            if score >= self.min_strength:
                swings.append({
                    "index": i,
                    "price": highs[i],
                    "type": "high",
                    "strength": score,
                    "timestamp": self.candles[i].end_time,
                })

        for i in swing_lows:
            score = self._compute_swing_score(i, highs, lows, kind="low", swings=swings)
            if score >= self.min_strength:
                swings.append({
                    "index": i,
                    "price": lows[i],
                    "type": "low",
                    "strength": score,
                    "timestamp": self.candles[i].end_time,
                })

        # Tri et conservation des swings récents
        swings = sorted(swings, key=lambda x: x["timestamp"])
        if swings:
            self.current_swings = swings[-20:]  # garder les 20 derniers
            self.strong_swings = [s for s in swings if s["strength"] > 1.5]

            last = swings[-1]
            self.last_swing_type = last["type"]
            if last["type"] == "high":
                self.last_swing_high = last["price"]
            else:
                self.last_swing_low = last["price"]

        await self._publish(timestamp)
        # self._log_strong_swings(self.strong_swings)


    def _log_strong_swings(self, swings):
        """Affiche un log lisible des swings forts détectés"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        simple_log = [
            {
                "index": s["index"],
                "type": s["type"],
                "price": round(s["price"], 2),
                "strength": round(s["strength"], 3),
                "timestamp": s["timestamp"].isoformat(),
            }
            for s in swings
        ]
        print(f"{ts} [SwingDetector] Swings forts détectés : {json.dumps(simple_log, indent=2)}")


    def _detect_swings(self, highs, lows):
        """Détecte les index de swings (simples)."""
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

    # =====================================================
    # Calcul du score combiné (force, dominance, rejet)
    # =====================================================
    def _compute_swing_score(self, i, highs, lows, kind="high", swings=None):
        """Score combiné pour évaluer la qualité d’un swing."""
        if swings is None:
            swings = []

        strength = self._compute_strength(i, highs, lows, kind)
        dominant = 1.0 if self._is_structurally_dominant(i, swings, highs, lows, kind) else 0.5
        rejection = self._compute_rejection_ratio(self.candles[i])

        # Adaptation du seuil selon la volatilité
        volatility = np.std(highs[-self.lookback:] - lows[-self.lookback:])
        mean_volatility = np.mean(highs[-50:] - lows[-50:]) if len(highs) > 50 else volatility
        volatility_factor = 1.2 if volatility < mean_volatility * 0.5 else 1.0

        score = (strength * 0.6) + (dominant * 0.2) + (rejection * 0.2)
        return score / volatility_factor

    def _compute_strength(self, i, highs, lows, kind="high"):
        """Force relative du swing par rapport à l’ATR local."""
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

    def _is_structurally_dominant(self, i, swings, highs, lows, kind="high"):
        """Vérifie que le swing dépasse clairement les précédents swings similaires."""
        last_swings = [s["price"] for s in swings if s["type"] == kind][-3:]
        if not last_swings:
            return True
        if kind == "high":
            return highs[i] > max(last_swings)
        else:
            return lows[i] < min(last_swings)

    def _compute_rejection_ratio(self, candle):
        """Mesure le rejet par la taille relative de la mèche opposée."""
        total = candle.high - candle.low
        if total == 0:
            return 0
        upper_wick = candle.high - max(candle.close, candle.open)
        lower_wick = min(candle.close, candle.open) - candle.low
        if candle.close < candle.open:
            # Bougie rouge → rejet haussier (mèche basse)
            return lower_wick / total
        else:
            # Bougie verte → rejet baissier (mèche haute)
            return upper_wick / total

    # =====================================================
    # Publication
    # =====================================================
    async def _publish(self, timestamp: datetime):
        """Publie les swings détectés."""
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
                    "strong_swings": self.strong_swings,
                    "lookback": self.lookback,
                    "min_distance": self.min_distance,
                    "min_strength": self.min_strength,
                },
            )
        )

    async def run(self):
        """Mode événementiel — pas de boucle."""
        pass
