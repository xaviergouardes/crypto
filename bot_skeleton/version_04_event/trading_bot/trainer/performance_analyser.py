import pandas as pd
from trading_bot.core.logger import Logger

class PerformanceAnalyzer:
    """
    Classe pour analyser les performances d'une série de trades.
    Fournit des statistiques individuelles et un score global normalisé.
    """

    _logger = Logger.get("PerformanceAnalyzer")

    def __init__(self):
        pass

    def stats_one_line(self, stats: dict):
        """
        Retourne un résumé compact d'une backtest stats.
        """
        ts = stats.get("trading_system", {})
        return (
            f"Backtest #{stats['id']} | "
            f"Profit: {stats['total_profit']:.2f} | "
            f"Win rate: {stats['win_rate']*100:.1f}% | "
            f"Trades: {stats['num_trades']} | "
            f"Max DD: {stats['max_drawdown_pct']:.1f}% | "
            f"Max Win Streak: {stats['max_winning_streak']} | "
            f"SW: {ts.get('swing_window', '')} | "
            f"TP: {ts.get('tp_pct', '')} | SL: {ts.get('sl_pct', '')}"
        )

    def analyze(self, trades_list, params=None, name=None, bot_id=None, initial_capital=1000.0):
        """
        Transforme une liste de trades en stats et calcule les indicateurs principaux.
        
        Args:
            trades_list : liste de dicts avec au moins "pnl" (profit/loss)
            params : dict des paramètres du bot/trading system
            name : nom du bot
            bot_id : identifiant du bot
            initial_capital : capital initial pour calcul du max drawdown (%)
        
        Returns:
            stats : dict léger avec indicateurs principaux
            trades_list : journal complet
        """
        params = params or {}
        df = pd.DataFrame(trades_list) if trades_list else pd.DataFrame()

        total_profit = df["pnl"].sum() if not df.empty else 0
        win_rate = (len(df[df["pnl"] > 0]) / len(df)) if not df.empty else 0
        num_trades = len(df)
        max_drawdown_pct = self._compute_max_drawdown_pct(df, initial_capital)
        max_winning_streak = self._compute_max_winning_streak(df)

        self._logger.debug(
            f"→ [{bot_id}] Profit: {total_profit:.2f}, Win Rate: {win_rate:.2%}, "
            f"Trades: {num_trades}, Max DD: {max_drawdown_pct:.1f}%, Max Win Streak: {max_winning_streak}"
        )

        stats = {
            "id": bot_id,
            "name": name,
            "total_profit": total_profit,
            "win_rate": win_rate,
            "num_trades": num_trades,
            "max_drawdown_pct": max_drawdown_pct,
            "max_winning_streak": max_winning_streak,
            **params
        }

        return stats, trades_list

    def compute_total_score(self, df, perf_cols=None):
        """
        Calcule un score normalisé moyen sur les colonnes de performance.
        """
        perf_cols = perf_cols or ["total_profit", "win_rate", "num_trades", "max_drawdown_pct", "max_winning_streak"]
        score_df = pd.DataFrame(index=df.index)

        for col in perf_cols:
            if col not in df.columns:
                continue
            vals = df[col].astype(float)
            mi, ma = vals.min(), vals.max()
            if ma == mi:
                score_df[col] = 1
            elif col == "max_drawdown_pct":
                # On inverse car moins c'est mieux
                score_df[col] = 1 - (vals - mi) / (ma - mi)
            else:
                score_df[col] = (vals - mi) / (ma - mi)

        df["total_score"] = score_df.mean(axis=1)
        return df

    @staticmethod
    def _compute_max_drawdown_pct(df, initial_capital=1000.0):
        """
        Calcule la perte maximale en pourcentage du capital initial.
        """
        if df.empty or "pnl" not in df.columns:
            return 0.0
        equity = (df["pnl"].cumsum() + initial_capital).values
        peak = equity[0]
        max_dd = 0.0
        for e in equity:
            peak = max(peak, e)
            dd = peak - e
            if dd > max_dd:
                max_dd = dd
        return (max_dd / initial_capital) * 100.0

    @staticmethod
    def _compute_max_winning_streak(df):
        """
        Calcule le nombre maximal de trades gagnants consécutifs.
        """
        if df.empty or "pnl" not in df.columns:
            return 0
        streak = 0
        max_streak = 0
        for pnl in df["pnl"]:
            if pnl > 0:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
        return max_streak
