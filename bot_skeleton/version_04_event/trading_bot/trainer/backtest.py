
import asyncio

import pandas as pd

from trading_bot.bots.bot import Bot
from trading_bot.core.logger import Logger
from trading_bot.trainer.statistiques_engine import *

class Backtest:

    logger = Logger.get("Backtest")

    def __init__(self, bot_type:str=None):
        self._bot_type = bot_type

    async def execute(self, params: dict = None):
 
        self.logger.info(f"Backtest avec params={params}")

        bot = Bot(self._bot_type, "bot_01")

        bot.set_backtest_mode()
        bot.sync(params)

        trades_list = await bot.start()

        stats, trades_list = bot.get_stats()

        self.logger.debug(" | ".join(f"{k}: {float(v):.4f}" if isinstance(v, float) or hasattr(v, 'item') else f"{k}: {v}" for k, v in stats.items()))
        self.logger.info("Backtest Terminé !")

        return stats, trades_list


if __name__ == "__main__":

    import logging
    from trading_bot.bots.bot import Bot

    Logger.set_default_level(logging.INFO)

    # # Niveau spécifique pour
    # Logger.set_level("IndicatorAtr", logging.DEBUG)
    # Logger.set_level("RSICrossSignalEngine", logging.DEBUG)
    # Logger.set_level("IndicatorRSI", logging.DEBUG)
    # Logger.set_level("Backtest", logging.INFO)
    # Logger.set_level("IndicatorEmaCrossDetector", logging.DEBUG)
    # Logger.set_level("MaCrossFastSlowSignalEngine", logging.DEBUG)
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    Logger.set_level("TradeJournal", logging.INFO)

    params = {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20251014_20251214.csv",
        "symbol": "ethusdc",
        "interval": "5m",
        "initial_capital": 1000,
        "trading_system": {
            "filter": True,
            "rsi_fast_period": 5,
            "rsi_slow_period": 21,
            "atr_period":14,
            "tp_pct": 2,
            "sl_pct": 1
        }
    }

    backtest_executor = Backtest("rsi_cross_bot")
    stats, trades_list = asyncio.run(backtest_executor.execute(params)) 

    # Backtest.logger.info(" | ".join(f"{k}: {float(v):.4f}" if isinstance(v, float) or hasattr(v, 'item') else f"{k}: {v}" for k, v in stats.items()))
    Backtest.logger.info(f"trades_list : {trades_list}")

 