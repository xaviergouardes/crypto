
import asyncio

import pandas as pd

from trading_bot.core.logger import Logger
from trading_bot.trainer.statistiques_engine import *

class Backtest:

    logger = Logger.get("Backtest")

    def __init__(self, bot_class):
        self._bot_class = bot_class
        self.stats_engine = StatsEngine(indicators=[
            TotalProfitIndicator(),
            WinRateIndicator(),
            NumTradesIndicator(),
            MaxDrawdownIndicator(),
            MaxWinningStreakIndicator(),
            NormalizedScoreIndicator(weights={
                "s_total_profit": 0.3,
                "s_win_rate": 0.4,
                "s_max_drawdown_pct": 0.2,
                "s_num_trades": 0.1
            })
        ])

    async def execute(self, params: dict = None):
 
        self.logger.info(f"Backtest avec params={params}")

        bot = self._bot_class()

        bot.stop()
        bot.set_backtest_mode()
        bot.sync(params)

        trades_list = await bot.start()

        # Analyse via StatsEngine
        stats, trades_list = self.stats_engine.analyze(
            df=pd.DataFrame(trades_list),
            params={**params}
        )

        self.logger.debug(" | ".join(f"{k}: {float(v):.4f}" if isinstance(v, float) or hasattr(v, 'item') else f"{k}: {v}" for k, v in stats.items()))
        self.logger.info("Backtest Terminé !")

        return stats, trades_list


if __name__ == "__main__":

    import logging
    from trading_bot.bots.sweep_bot import SweepBot

    Logger.set_default_level(logging.INFO)

    # # Niveau spécifique pour
    Logger.set_level("Backtest", logging.DEBUG)
    # Logger.set_level("BacktestEngine", logging.INFO)
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)

    params = {
        "trading_system": {
            "swing_window": 21,
            "tp_pct": 2.0,
            "sl_pct": 2.0,
            "swing_side": 3,
        }
    }

    # backtest_executor = Backtest(BOT_CLASSES["sweep_bot"])
    # stats, trades_list = asyncio.run(backtest_executor.execute(params)) 

    # Backtest.logger.info(" | ".join(f"{k}: {float(v):.4f}" if isinstance(v, float) or hasattr(v, 'item') else f"{k}: {v}" for k, v in stats.items()))
    # Backtest.logger.info(f"trades_list : {trades_list}")

 