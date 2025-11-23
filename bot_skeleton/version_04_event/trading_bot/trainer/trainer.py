from itertools import product
import logging
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor

from trading_bot.core.logger import Logger
from trading_bot.trainer.backtest_executor import BacktestExecutor


class BotTrainer:
    logger = Logger.get("BotTrainer")

    def __init__(self, bot):
        self.bot_class = bot.__class__      # garder la classe pour ré-instancier
        self.params = bot.params.copy()     # paramètres de base

    def compute_valid_combinations(self, param_grid):
        """Génère toutes les combinaisons valides avec les paramètres statiques self.params."""
        rules = [
            lambda p: p["tp_pct"] >= p["sl_pct"],  # Take profit >= Stop loss
        ]

        keys, values = zip(*param_grid.items())
        param_combinations = [dict(zip(keys, v)) for v in product(*values)]

        full_param_sets = []
        for combo in param_combinations:
            full_params = self.params.copy()
            full_params.update(combo)
            if all(rule(full_params) for rule in rules):
                full_param_sets.append(full_params)

        return full_param_sets

    ###########################################################################
    # 1) Exécution d'un backtest sur un set de paramètres
    ###########################################################################
    def _sync_run_single_bot(self, idx, params):
        """Exécution synchrone pour ThreadPoolExecutor"""
        async def _async_execute():
            bot_name = f"Bot_{idx}"
            self.logger.debug(f"[{idx}] Running Bot with params: {params}")

            # Créer une instance du bot et du BacktestExecutor
            bot_instance = self.bot_class(params.copy())
            executor = BacktestExecutor(bot_instance)
            await executor.execute(params)

            # --- Transformation du journal en DataFrame ---
            trades_list = bot_instance.system_trading.trader_journal.trades
            df_journal = pd.DataFrame(trades_list) if trades_list else pd.DataFrame()

            total_profit = df_journal["pnl"].sum() if not df_journal.empty else 0
            win_rate = (
                len(df_journal[df_journal["pnl"] > 0]) / len(df_journal)
                if not df_journal.empty else 0
            )

            self.logger.debug(
                f"    → [{idx}] Total Profit: {total_profit:.2f}, Win Rate: {win_rate:.2%}"
            )

            return {
                "name": bot_name,
                "total_profit": total_profit,
                "win_rate": win_rate,
                "num_trades": len(df_journal),
                **params,
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

        return summary_df, results


if __name__ == "__main__":
    from trading_bot.bots.sweep_bot import SweepBot

    # Niveau global : silence tout sauf WARNING et plus
    Logger.set_default_level(logging.ERROR)

    # Niveau spécifique pour
    Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)

    # param_grid = {
    #     "swing_window": [21, 50, 100, 150, 200],
    #     "tp_pct": [1.0, 1.5, 2, 2.5],
    #     "sl_pct": [0.5, 1.0, 1.5, 2]
    # }

    param_grid = {
        "swing_window": [200],
        "tp_pct": [2, 2.5],
        "sl_pct": [0.5, 1.0]
    }

    params = {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "5m",
        "initial_capital": 1000,
        "swing_window": 150,
        "swing_side": 2,
        "tp_pct": 2,
        "sl_pct": 0.5
    }

    bot = SweepBot(params)
    trainer = BotTrainer(bot)
    summary_df, results = asyncio.run(trainer.run(param_grid))

    pd.set_option('display.max_rows', None)
    # pd.set_option("display.max_columns", None)
    print(summary_df[["name", "total_profit", "win_rate", "num_trades", "total_score", "swing_window", "tp_pct", "sl_pct"]])
