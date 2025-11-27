from itertools import product
import logging
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor

from trading_bot.bots import BOT_CLASSES
from trading_bot.core.logger import Logger
from trading_bot.trainer.backtest import Backtest
from trading_bot.trainer.performance_analyser import PerformanceAnalyzer


class BotTrainer:
    logger = Logger.get("BotTrainer")

    def __init__(self, bot_class):
        self._bot_class = bot_class      # garder la classe pour ré-instancier
 
    def _all_param_grids(self, param_grid):
        """Génère toutes les combinaisons valides avec les règles appliquées."""
        rules = [
            lambda p: p['trading_system']['tp_pct'] >= p['trading_system']['sl_pct'],  # Take profit >= Stop loss
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
            bt_executor = Backtest(self._bot_class)
            stats, trades_list = await bt_executor.execute(params)

            performance_analyser = PerformanceAnalyzer()
            stats, trades_list = performance_analyser.analyze(
                trades_list=trades_list,
                params=params,
                name=bot_name,
                bot_id=idx
            )
            self.logger.debug( performance_analyser.stats_one_line(stats))

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

        summary_df = pd.DataFrame(results)

        performance_analyser = PerformanceAnalyzer()
        summary_df = performance_analyser.compute_total_score(summary_df)

        self.log_summary_df_one_line(summary_df)

        return summary_df, results



    def log_summary_df_one_line(self, df, col_width=12, float_precision=2):
        """
        Affiche le DataFrame df sur une seule ligne par entrée avec colonnes de largeur fixe.
        Tout l’aplatissement des colonnes trading_system -> systrad_xxx est fait ici.
        """
        display_df = df.copy()

        # 1. Aplatir trading_system si présent
        systrad_cols = []
        if "trading_system" in display_df.columns:
            for k in display_df["trading_system"].iloc[0].keys():
                col_name = f"p_{k}"
                display_df[col_name] = display_df["trading_system"].apply(lambda r: r.get(k, ""))
                systrad_cols.append(col_name)
            display_df = display_df.drop(columns=["trading_system"])

        # 2. Colonnes à afficher : base + systrad_xxx dynamiques
        base_cols = ["name", "total_profit", "win_rate", "num_trades", "total_score",
                    "max_drawdown_pct", "max_winning_streak"] 
        cols_to_show = base_cols + systrad_cols

        # 3. Préparer l'en-tête
        header = " | ".join(f"{col[:col_width]:<{col_width}}" for col in cols_to_show)
        self.logger.info(header)
        self.logger.info("-" * len(header))

        # 4. Affichage ligne par ligne
        for _, row in display_df.iterrows():
            line_items = []
            for col in cols_to_show:
                val = row[col]
                val_str = f"{val:.{float_precision}f}" if isinstance(val, float) else str(val)
                line_items.append(f"{val_str[:col_width]:<{col_width}}")
            self.logger.info(" | ".join(line_items))


if __name__ == "__main__":
    from trading_bot.bots.sweep_bot import SweepBot

    # Niveau global : silence tout sauf WARNING et plus
    Logger.set_default_level(logging.WARNING)

    # Niveau spécifique pour
    Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("Backtest", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)

    # param_grid = {
    #     "swing_window": [21, 50, 100, 150, 200],
    #     "tp_pct": [1.0, 1.5, 2, 2.5],
    #     "sl_pct": [0.5, 1.0, 1.5, 2],
    #     "swing_side": [2, 3]
    # }

    param_grid = {
        "trading_system": {
            "swing_window": [200],
            "tp_pct": [2.0, 2.5],
            "sl_pct": [1.0]
        }
    }

    trainer = BotTrainer(BOT_CLASSES["sweep_bot"])
    summary_df, results = asyncio.run(trainer.run(param_grid))
    # print(summary_df.columns)

    pd.set_option('display.max_rows', None)
    # pd.set_option("display.max_columns", None)
    # print(summary_df[["name", "total_profit", "win_rate", "num_trades", "total_score", "swing_window", "tp_pct", "sl_pct"]])
