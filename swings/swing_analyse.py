import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json

# ----------------------------------------------------
# Classe Candle
# ----------------------------------------------------
class Candle:
    def __init__(self, timestamp, open_, high, low, close):
        self.end_time = timestamp
        self.open = open_
        self.high = high
        self.low = low
        self.close = close

# ----------------------------------------------------
# Simple détecteur de swings forts
# ----------------------------------------------------
class SimpleSwingDetector:
    def __init__(self, candles, lookback=3, min_distance=5, min_strength=1.5):
        self.candles = candles
        self.lookback = lookback
        self.min_distance = min_distance
        self.min_strength = min_strength
        self.strong_swings = []

    def detect_swings(self):
        highs = np.array([c.high for c in self.candles])
        lows = np.array([c.low for c in self.candles])
        n = self.lookback
        swing_highs, swing_lows = [], []

        # Détection simple
        for i in range(n, len(highs) - n):
            if highs[i] == max(highs[i - n:i + n + 1]):
                if not swing_highs or (i - swing_highs[-1]) >= self.min_distance:
                    swing_highs.append(i)
            if lows[i] == min(lows[i - n:i + n + 1]):
                if not swing_lows or (i - swing_lows[-1]) >= self.min_distance:
                    swing_lows.append(i)

        # Calcul force (simplifiée)
        for i in swing_highs:
            strength = (highs[i] - np.min(lows[max(0, i-n):i+n])) / np.mean(highs[max(0, i-n):i+n]-lows[max(0,i-n):i+n])
            if strength >= self.min_strength:
                self.strong_swings.append({"index": i, "price": highs[i], "type": "high", "strength": strength, "timestamp": self.candles[i].end_time})

        for i in swing_lows:
            strength = (np.max(highs[max(0, i-n):i+n]) - lows[i]) / np.mean(highs[max(0, i-n):i+n]-lows[max(0,i-n):i+n])
            if strength >= self.min_strength:
                self.strong_swings.append({"index": i, "price": lows[i], "type": "low", "strength": strength, "timestamp": self.candles[i].end_time})

        self.strong_swings.sort(key=lambda x: x["index"])
        return self.strong_swings

# ----------------------------------------------------
# Fonction pour tracer
# ----------------------------------------------------
def plot_swings(candles, swings):
    closes = [c.close for c in candles]
    times = [c.end_time for c in candles]

    plt.figure(figsize=(14,6))
    plt.plot(times, closes, color="gray", label="Close")

    for s in swings:
        color = "red" if s["type"] == "high" else "green"
        plt.scatter(times[s["index"]], s["price"], color=color, s=80, label=s["type"].upper())

    plt.title("Swings détectés")
    plt.legend()
    plt.show()

# ----------------------------------------------------
# Lecture du CSV et filtrage selon période
# ----------------------------------------------------
def load_candles_from_csv(file_path, period_minutes=3):
    df = pd.read_csv(file_path, parse_dates=["timestamp"])
    
    # Optionnel : resample si période différente
    if period_minutes != 3:
        df.set_index("timestamp", inplace=True)
        df = df.resample(f"{period_minutes}T").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last"
        }).dropna().reset_index()

    candles = [Candle(row["timestamp"], row["open"], row["high"], row["low"], row["close"]) for _, row in df.iterrows()]
    return candles

# ----------------------------------------------------
# Statistiques simples
# ----------------------------------------------------
def analyze_swings(swings):
    if not swings:
        print("Pas de swings détectés")
        return

    highs = [s for s in swings if s["type"] == "high"]
    lows = [s for s in swings if s["type"] == "low"]
    avg_strength_high = np.mean([s["strength"] for s in highs]) if highs else 0
    avg_strength_low = np.mean([s["strength"] for s in lows]) if lows else 0
    avg_spacing = np.mean(np.diff([s["index"] for s in swings])) if len(swings) > 1 else 0

    print(f"Nombre total de swings : {len(swings)}")
    print(f"Nombre de HIGH : {len(highs)}, force moyenne : {avg_strength_high:.2f}")
    print(f"Nombre de LOW : {len(lows)}, force moyenne : {avg_strength_low:.2f}")
    print(f"Espacement moyen entre swings : {avg_spacing:.1f} bougies")

# ----------------------------------------------------
# Exemple d'utilisation
# ----------------------------------------------------
if __name__ == "__main__":
    file_path = "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHUSDC_3m_historique_20250901_20251017.csv"  # ton CSV
    period = 3  # minutes
    candles = load_candles_from_csv(file_path, period_minutes=period)

    detector = SimpleSwingDetector(candles)
    swings = detector.detect_swings()

    plot_swings(candles, swings)
    analyze_swings(swings)

    with open("swings_debug.json", "w") as f:
        json.dump(swings, f, default=str, indent=2)
