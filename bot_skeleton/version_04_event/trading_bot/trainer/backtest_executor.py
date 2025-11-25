
import asyncio

from trading_bot.core.logger import Logger

class BacktestExecutor:

    logger = Logger.get("BacktestExecutor")

    def __init__(self, bot):
        self._bot = bot

    async def execute(self, params: dict = None):
 
        self.logger.debug(f"Backtest avec params={params}")

        self._bot.stop()
        self._bot.set_backtest_mode()
        self._bot.sync(params)

        stats = await self._bot.start()
        return stats


if __name__ == "__main__":

    import logging
    from trading_bot.bots.sweep_bot import SweepBot

    Logger.set_default_level(logging.INFO)

    # Niveau spécifique pour
    Logger.set_level("BacktestEngine", logging.DEBUG)
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)

    params = {
        "swing_window": 21,
        "tp_pct": 2.5,
        "sl_pct": 0.5,
    }

    bot = SweepBot()
    backtest_executor = BacktestExecutor(bot)
    stats = asyncio.run(backtest_executor.execute(params)) 

    # self.engine = BacktestEngine(self.event_bus, self.system_trading, self.params)
    # stats = await self.engine.run()
    BacktestExecutor.logger.info(f"Statistiques : {stats}")

 