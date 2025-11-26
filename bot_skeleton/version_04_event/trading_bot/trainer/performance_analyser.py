import pandas as pd
from trading_bot.core.logger import Logger

class PerformanceAnalyzer:

    _logger = Logger.get("PerformanceAnalyzer")

    def __init__(self):
        pass

    def stats_one_line(self, stats:dict):
        return (
            f"Backtest #{stats['id']} | "
            f"Profit: {stats['total_profit']:.2f} | "
            f"Win rate: {stats['win_rate']*100:.1f}% | "
            f"Trades: {stats['num_trades']} | "
            f"SW: {stats['swing_window']} | "
            f"TP: {stats['tp_pct']} | SL: {stats['sl_pct']}"
        )
    
    def analyze(self, trades_list, params=None, name=None, bot_id=None):
        """
        Transforme une liste de trades en DataFrame + calcule les performances.
        Renvoie **deux valeurs distinctes** :
            - stats : dict léger
            - journal : DataFrame complet
        """

        params = params or {}

        # Journal en DataFrame
        df_trades_list = pd.DataFrame(trades_list) if trades_list else pd.DataFrame()

        # Calculs de performance
        total_profit = df_trades_list["pnl"].sum() if not df_trades_list.empty else 0

        win_rate = (
            len(df_trades_list[df_trades_list["pnl"] > 0]) / len(df_trades_list)
            if not df_trades_list.empty else 0
        )

        num_trades = len(df_trades_list)

        # Log
        self._logger.debug(
            f"→ [{bot_id}] Total Profit: {total_profit:.2f}, Win Rate: {win_rate:.2%} ({num_trades} trades)"
        )

        # Stats simples à mettre dans des DataFrames
        stats = {
            "id": bot_id,
            "name": name,
            "total_profit": total_profit,
            "win_rate": win_rate,
            "num_trades": num_trades,
            **params
        }

        # On retourne stats SEULEMENT + journal séparé
        return stats, trades_list
