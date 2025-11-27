
import asyncio

from trading_bot.bots import BOT_CLASSES
from trading_bot.core.logger import Logger
from trading_bot.trainer.performance_analyser import PerformanceAnalyzer

class Backtest:

    logger = Logger.get("Backtest")

    def __init__(self, bot_class):
        self._bot_class = bot_class

    async def execute(self, params: dict = None):
 
        self.logger.info(f"Backtest avec params={params}")

        bot = self._bot_class()

        bot.stop()
        bot.set_backtest_mode()
        bot.sync(params)

        trades_list = await bot.start()

        performance_analyser = PerformanceAnalyzer()
        stats, trades_list = performance_analyser.analyze(
            trades_list=trades_list,
            params=params,
            name="Backtest",
            bot_id=1
        )
        self.logger.info(performance_analyser.stats_one_line(stats))

        return stats, trades_list


if __name__ == "__main__":

    import logging
    from trading_bot.bots.sweep_bot import SweepBot

    Logger.set_default_level(logging.INFO)

    # # Niveau spécifique pour
    # Logger.set_level("Backtest", logging.DEBUG)
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

    backtest_executor = Backtest(BOT_CLASSES["sweep_bot"])
    stats, trades_list = asyncio.run(backtest_executor.execute(params)) 

    # Backtest.logger.info(
    #     f"Backtest #{stats['id']} | "
    #     f"Profit: {stats['total_profit']:.2f} | "
    #     f"Win rate: {stats['win_rate']*100:.1f}% | "
    #     f"Trades: {stats['num_trades']} | "
    #     f"SW: {stats['swing_window']} | "
    #     f"TP: {stats['tp_pct']} | SL: {stats['sl_pct']}"
    # )
    # # Backtest.logger.info(f"Journal : {journal}")

 