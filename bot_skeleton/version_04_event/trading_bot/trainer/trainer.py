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
            lambda p: p["tp_pct"] >= p["sl_pct"],  # Take profit >= Stop loss
        ]

        keys, values = zip(*param_grid.items())
        param_combinations = [dict(zip(keys, v)) for v in product(*values)]

        # Appliquer les règles de filtrage
        valid_combinations = [
            p for p in param_combinations
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

        # --- DataFrame plat avec performances et paramètres ---
        summary_df = pd.DataFrame(results)

        # Calcul total_score
        perf_cols = ["total_profit", "win_rate", "num_trades"]
        score_df = pd.DataFrame(index=summary_df.index)
        for col in perf_cols:
            vals = summary_df[col].astype(float)
            mi, ma = vals.min(), vals.max()
            score_df[col] = 1 if ma == mi else (vals - mi) / (ma - mi)
        summary_df["total_score"] = score_df.mean(axis=1)

        # Tri par total_score décroissant
        summary_df = summary_df.sort_values("total_score", ascending=False).reset_index(drop=True)

        # Todo : attention la liste des paramétre est dépendante du bot / signal engine
        cols_to_show = ["name", "total_profit", "win_rate", "num_trades", "total_score", "swing_window", "tp_pct", "sl_pct"]
        self.log_summary_df_one_line(self.logger, summary_df, cols=cols_to_show)

        return summary_df, results


    def log_summary_df_one_line(self, logger, df, cols=None, col_width=12, float_precision=2):
        """
        Affiche le DataFrame df sur une seule ligne par entrée avec colonnes de largeur fixe.
        
        Args:
            logger : logger à utiliser
            df : DataFrame pandas
            cols : liste des colonnes à afficher (None pour toutes)
            col_width : largeur fixe des colonnes
            float_precision : nb de décimales pour les floats
        """
        if cols is None:
            cols = df.columns.tolist()

        # Préparer l'en-tête
        header = " | ".join(f"{col[:col_width]:<{col_width}}" for col in cols)
        logger.info(header)
        logger.info("-" * len(header))

        # Parcourir les lignes et formater
        for _, row in df.iterrows():
            line_items = []
            for col in cols:
                val = row[col]
                if isinstance(val, float):
                    # Arrondi et converti en str
                    val_str = f"{val:.{float_precision}f}"
                else:
                    val_str = str(val)
                # tronquer ou remplir pour largeur fixe
                line_items.append(f"{val_str[:col_width]:<{col_width}}")
            line = " | ".join(line_items)
            logger.info(line)


if __name__ == "__main__":
    from trading_bot.bots.sweep_bot import SweepBot

    # Niveau global : silence tout sauf WARNING et plus
    Logger.set_default_level(logging.WARNING)

    # Niveau spécifique pour
    Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("Backtest", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)

    param_grid = {
        "swing_window": [21, 50, 100, 150, 200],
        "tp_pct": [1.0, 1.5, 2, 2.5],
        "sl_pct": [0.5, 1.0, 1.5, 2],
        "swing_side": [2, 3]
    }

    # param_grid = {
    #     "swing_window": [200],
    #     "tp_pct": [2.0, 2.5],
    #     "sl_pct": [1.0]
    # }

    trainer = BotTrainer(BOT_CLASSES["sweep_bot"])
    summary_df, results = asyncio.run(trainer.run(param_grid))
    # print(summary_df.columns)

    pd.set_option('display.max_rows', None)
    # pd.set_option("display.max_columns", None)
    # print(summary_df[["name", "total_profit", "win_rate", "num_trades", "total_score", "swing_window", "tp_pct", "sl_pct"]])
