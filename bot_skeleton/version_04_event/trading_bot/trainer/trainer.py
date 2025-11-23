from itertools import product
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor

from trading_bot.core.logger import Logger


class BotTrainer:

    logger = Logger.get("BotTrainer")

    def __init__(self, bot_class, params):
        self.bot_class = bot_class
        self.params = params

    def compute_valid_combinations(self, param_grid):
        """
        Génère toutes les combinaisons possibles et fusionne avec les paramètres statiques self.params.
        Permet de filtrer les combinaisons avec des règles personnalisées.

        Args:
            param_grid (dict): paramètres variables à combiner
            rules (list of callables): chaque fonction prend un dict de paramètres et retourne True si valide

        Returns:
            list of dict: liste de combinaisons valides fusionnées avec self.params
        """

        # Règles pour filtrer les combinaisons => on garde si c'est vrai
        rules = [
            lambda p: p["tp_pct"] >= p["sl_pct"],   # Take profit >= Stop loss
        ]

        keys, values = zip(*param_grid.items())
        param_combinations = [dict(zip(keys, v)) for v in product(*values)]

        full_param_sets = []
        for combo in param_combinations:
            full_params = self.params.copy()
            full_params.update(combo)

            # Vérification des règles
            if rules:
                valid = all(rule(full_params) for rule in rules)
                if not valid:
                    continue

            full_param_sets.append(full_params)

        return full_param_sets


    ###########################################################################
    # 1) Exécution d'un bot dans un THREAD
    ###########################################################################
    def _sync_run_single_bot(self, idx, params):

        async def _async_execute():
 
            self.logger.debug(f"[{idx}] Running Bot with params: {params}")

            bot = self.bot_class(params, "backtest")
            bot.system_trading.compute_warmup_count()
            await bot.run()

            # Journal trades
            journal = bot.system_trading.trader_journal.trades
            df_journal = pd.DataFrame(journal)

            total_profit = df_journal["pnl"].sum() if not df_journal.empty else 0
            win_rate = (
                len(df_journal[df_journal["pnl"] > 0]) / len(df_journal)
                if len(df_journal) > 0 else 0
            )


            self.logger.debug(
                    f"    → [{idx}] Total Profit: {total_profit:.2f}, Win Rate: {win_rate:.2%}\n"
                )

            return {
                "name": f"Bot_{idx}",
                "total_profit": total_profit,
                "win_rate": win_rate,
                "num_trades": len(df_journal),
                **params,  # paramètres réels intégrés directement
                "journal": df_journal.copy()
            }

        return asyncio.run(_async_execute())

    ###########################################################################
    # 2) Exécution complète (ThreadPool + async)
    ###########################################################################
    async def run(self, param_grid, verbose=True, max_workers=10):

        full_param_sets = self.compute_valid_combinations(param_grid)
        total_passages = len(full_param_sets)

        results = []
        loop = asyncio.get_event_loop()
        self.logger.info(f"🔧 Total combinaisons : {total_passages}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = []
            for idx, params in enumerate(full_param_sets, start=1):
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

        # DataFrame plat avec performances et paramètres
        summary_df = pd.DataFrame(results)

        # Calcul total_score directement dans le DataFrame
        perf_cols = ["total_profit", "win_rate", "num_trades"]
        score_df = pd.DataFrame(index=summary_df.index)
        for col in perf_cols:
            vals = summary_df[col].astype(float)
            mi, ma = vals.min(), vals.max()
            score_df[col] = 1 if ma == mi else (vals - mi) / (ma - mi)
        summary_df["total_score"] = score_df.mean(axis=1)

        # Tri par total_score décroissant
        summary_df = summary_df.sort_values("total_score", ascending=False).reset_index(drop=True)

        return summary_df, results
