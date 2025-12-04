import pandas as pd
from itertools import product
from trading_bot.core.logger import Logger

# --------------------------
# 1) Indicateurs
# il sont préfixés par s_ pour Statistique
# --------------------------
class BaseIndicator:
    """Interface pour un indicateur de performance"""
    def compute(self, df: pd.DataFrame, stats: dict, params: dict = None) -> dict:
        raise NotImplementedError()


class TotalProfitIndicator(BaseIndicator):
    def compute(self, df, stats, params=None):
        stats["s_total_profit"] = df["pnl"].sum() if not df.empty else 0
        return stats


class WinRateIndicator(BaseIndicator):
    def compute(self, df, stats, params=None):
        stats["s_win_rate"] = (len(df[df["pnl"] > 0]) / len(df)) if not df.empty else 0
        return stats


class NumTradesIndicator(BaseIndicator):
    def compute(self, df, stats, params=None):
        stats["s_num_trades"] = len(df)
        return stats


class MaxDrawdownIndicator(BaseIndicator):
    """
    < 5% → excellent
    5–12% → acceptable
    12–20% → risqué
    > 20% → très agressif, à surveiller
    """
    def compute(self, df, stats, params=None):
        if df.empty or "pnl" not in df.columns:
            stats["s_max_drawdown_pct"] = 0
            return stats
        capital_initial = params.get("capital_initial", 1000)
        cumulative = df["pnl"].cumsum()
        max_dd = ((cumulative.cummax() - cumulative).max() / capital_initial) * 100
        stats["s_max_drawdown_pct"] = max_dd
        return stats


class MaxWinningStreakIndicator(BaseIndicator):
    def compute(self, df, stats, params=None):
        if df.empty or "pnl" not in df.columns:
            stats["s_max_winning_streak"] = 0
            return stats
        streak = 0
        max_streak = 0
        for pnl in df["pnl"]:
            if pnl > 0:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
        stats["s_max_winning_streak"] = max_streak
        return stats

class NormalizedScoreIndicator(BaseIndicator):
    """
    Calcule un score normalisé basé sur plusieurs indicateurs.
    La normalisation se fait entre les bornes min/max passées en params
    ou par défaut sur la valeur de l’indicateur.
    """

    def __init__(self, weights=None):
        """
        weights: dict, pondérations par indicateur
        exemple: {"s_total_profit": 0.5, "s_win_rate": 0.3, "s_max_drawdown_pct": 0.2}
        """
        self.weights = weights or {}

    def compute(self, df, stats, params=None):
        stats = stats or {}
        # Récupérer les valeurs des indicateurs déjà calculés
        indicators = ["s_total_profit", "s_win_rate", "s_max_drawdown_pct", "s_max_winning_streak", "s_num_trades"]
        
        score = 0
        total_weight = 0
        for ind in indicators:
            w = self.weights.get(ind, 1)  # poids par défaut = 1
            val = stats.get(ind, 0)

            # Normalisation simple selon type
            if ind == "s_max_drawdown_pct":
                # Drawdown → moins c’est mieux, on inverse
                val_norm = max(0, 100 - val) / 100
            elif ind == "s_win_rate":
                val_norm = val  # déjà en 0-1
            elif ind == "s_total_profit":
                # On peut normaliser par capital initial si passé en params
                capital_initial = params.get("capital_initial", 1000)
                val_norm = val / (2 * capital_initial)  # heuristique, limite à 2x capital
                val_norm = min(1, max(0, val_norm))
            elif ind == "s_max_winning_streak":
                # On normalise arbitrairement sur 20 trades
                val_norm = min(1, val / 20)
            elif ind == "s_num_trades":
                max_trades = 100  # par exemple, on considère 100 trades = 1.0
                val_norm = min(val / max_trades, 1)
            else:
                val_norm = 0

            score += w * val_norm
            total_weight += w

        stats["s_normalized_score"] = score / total_weight if total_weight > 0 else 0
        return stats

# --------------------------
# 2) StatsEngine
# --------------------------
class StatsEngine:
    def __init__(self, indicators=None):
        self.indicators = indicators or []

    def analyze(self, df: pd.DataFrame, stats: dict = None, params: dict = None):

        stats = stats or {}
        params = params or {}

        # Aplatir trading_system dans les stats
        ts_params = params.get("trading_system", {})
        for k, v in ts_params.items():
            stats[f"p_{k}"] = v

        # Calcul des stats via les indicateurs
        for ind in self.indicators:
            stats = ind.compute(df, stats, params)

        return stats, df
