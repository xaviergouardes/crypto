from itertools import product
import logging
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor

from trading_bot.core.logger import Logger
from trading_bot.trainer.backtest import Backtest


class BotTrainer:
    logger = Logger.get("BotTrainer")

    def __init__(self, bot_type):
        self._bot_type = bot_type      # garder la classe pour ré-instancier
 
    def _all_param_grids(self, param_grid):
        """Génère toutes les combinaisons valides avec les règles appliquées."""
        rules = [
            lambda p: p['trading_system']['tp_pct'] >= p['trading_system']['sl_pct'],  # Take profit >= Stop loss
            lambda p: p['trading_system']['slow_period'] > p['trading_system']['fast_period'],  # Période longue > période courte pour les xMA
        ]

        if "trading_system" not in param_grid:
            return param_grid

        sys_grid = param_grid["trading_system"]
        keys, values = zip(*sys_grid.items())

        combinations = []
        for combo in product(*values):
            combinations.append({
                "trading_system": dict(zip(keys, combo))
            })

        # Appliquer les règles de filtrage
        valid_combinations = [
            p for p in combinations
            if all(rule(p) for rule in rules)
        ]

        return valid_combinations

    ###########################################################################
    # 1) Exécution d'un backtest sur un set de paramètres
    ###########################################################################
    def _sync_run_single_bot(self, idx, params):
        """Exécution synchrone pour ThreadPoolExecutor"""
        async def _async_execute():
            bot_name = f"Bot_{idx}"
            self.logger.debug(f"[{idx}] Running Bot with params: {params}")

            # Créer une instance du bot et du Backtest
            bt_executor = Backtest(self._bot_type)
            stats, trades_list = await bt_executor.execute(params)
            
            # Ajouter le nom du bot dans les stats
            stats["name"] = bot_name
 
            self.logger.debug(" | ".join(f"{k}: {float(v):.4f}" if isinstance(v, float) or hasattr(v, 'item') else f"{k}: {v}" for k, v in stats.items()))

            return stats

        return asyncio.run(_async_execute())

    ###########################################################################
    # 2) Exécution complète (ThreadPool + async)
    ###########################################################################
    async def run(self, param_grid, verbose=True, max_workers=10):
        all_param_grids = self._all_param_grids(param_grid)
        total_passages = len(all_param_grids)
        results = []
        loop = asyncio.get_event_loop()

        self.logger.info(f"🔧 Total combinaisons : {total_passages}")

        # -------------------------
        # 1. Exécution parallèle des bots
        # -------------------------
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = []
            for idx, params in enumerate(all_param_grids, start=1):
                if verbose:
                    self.logger.debug(f"[{idx}/{total_passages}] Scheduling bot…")
                task = loop.run_in_executor(
                    executor,
                    self._sync_run_single_bot,
                    idx,
                    params
                )
                tasks.append(task)

            done_count = 0
            for coro in asyncio.as_completed(tasks):
                result = await coro
                done_count += 1
                if verbose:
                    self.logger.info(f"✔ Progression : {done_count}/{total_passages} terminés")
                results.append(result)

        all_stats = pd.DataFrame(results)

        self.log_summary_df_one_line(all_stats)
        self.logger.info("Terminé !")
        return all_stats, results


    def log_summary_df_one_line(self, df, col_width=11, float_precision=2):
        """
        Log toutes les statistiques et paramètres d'un DataFrame en forme de tableau.
        Colonnes statistiques : préfixées par 's_'
        Colonnes paramètres : préfixées par 'p_'
        La colonne 'name' et 's_normalized_score' sont toujours affichées en premier si présentes.
        Les lignes sont triées par 's_normalized_score' décroissant.
        """
        if df.empty:
            self.logger.info("Aucun backtest à afficher.")
            return

        display_df = df.copy()

        # Trier par s_normalized_score si elle existe
        if "s_normalized_score" in display_df.columns:
            display_df = display_df.sort_values(by="s_normalized_score", ascending=False)

        # Colonnes statistiques et paramètres
        stat_cols = [c for c in display_df.columns if c.startswith("s_") and c != "s_normalized_score"]
        param_cols = [c for c in display_df.columns if c.startswith("p_")]
        other_cols = [c for c in display_df.columns if c not in stat_cols + param_cols + ["s_normalized_score"]]

        # Ordre final : name + s_normalized_score + autres stats + paramètres + reste
        cols_to_show = []
        if "name" in display_df.columns:
            cols_to_show.append("name")
        if "s_normalized_score" in display_df.columns:
            cols_to_show.append("s_normalized_score")
        cols_to_show += stat_cols + param_cols + [c for c in other_cols if c not in cols_to_show]

        # Préparer l'en-tête
        header = " | ".join(f"{col[:col_width]:<{col_width}}" for col in cols_to_show)
        self.logger.info(header)
        self.logger.info("-" * len(header))

        # Affichage ligne par ligne
        for _, row in display_df.iterrows():
            line_items = []
            for col in cols_to_show:
                val = row[col]
                # Formatage float ou np.float64
                if isinstance(val, (float, int)) or hasattr(val, "item"):
                    try:
                        val_str = f"{float(val):.{float_precision}f}"
                    except:
                        val_str = str(val)
                else:
                    val_str = str(val)
                line_items.append(f"{val_str[:col_width]:<{col_width}}")
            self.logger.info(" | ".join(line_items))





if __name__ == "__main__":
    # Niveau global : silence tout sauf WARNING et plus
    Logger.set_default_level(logging.WARNING)

    # Niveau spécifique pour
    Logger.set_level("BotTrainer", logging.INFO)
    Logger.set_level("Backtest", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)

    # param_grid = {
    #     "swing_window": [21, 50, 100, 150, 200],
    #     "tp_pct": [1.0, 1.5, 2, 2.5],
    #     "sl_pct": [0.5, 1.0, 1.5, 2],
    #     "swing_side": [2, 3]
    # }

    # param_grid = {
    #     "trading_system": {
    #         "swing_window": [200],
    #         "tp_pct": [2.0, 2.5],
    #         "sl_pct": [1.0]
    #     }
    # }

    # param_grid = {
    #     "trading_system": {
    #         "fast_period": [21, 50],
    #         "slow_period": [50, 100, 150 , 200],
    #         "min_gap": [0, 1],
    #         "slope_threshold": [0.5, 1, 1.5, 2],
    #         "tp_pct": [1.5, 2],
    #         "sl_pct": [1]
    #     }
    # }
    # param_grid = {
    #     "trading_system": {
    #         "fast_period": [21],
    #         "slow_period": [150],
    #         "min_gap": [0],
    #         "slope_threshold": [0.5],
    #         "tp_pct": [1.5],
    #         "sl_pct": [1]
    #     }
    # }
    # trainer = BotTrainer("ma_cross_fast_slow_bot")
    # summary_df, results = asyncio.run(trainer.run(param_grid))
    # print(summary_df.columns)


    param_grid = {
        "trading_system": {
            "warmup_count": [101],
            "fast_period": [5,14, 21],
            "slow_period": [21, 50, 75, 100],
            "tp_pct": [1, 2],
            "sl_pct": [0.5, 1]
        }
    }
    trainer = BotTrainer("rsi_cross_bot")
    summary_df, results = asyncio.run(trainer.run(param_grid))
    pd.set_option('display.max_rows', None)
    # pd.set_option("display.max_columns", None)
    # print(summary_df[["name", "total_profit", "win_rate", "num_trades", "total_score", "swing_window", "tp_pct", "sl_pct"]])
