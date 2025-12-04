import asyncio
from trading_bot.bots import BOT_CLASSES
from trading_bot.core.logger import Logger
from trading_bot.trainer.backtest import Backtest
from trading_bot.trainer.trainer import BotTrainer


class BotControler:
    _logger = Logger.get("BotManager")

    def __init__(self, bot_type, bot_id="bot_01"):
        self.bot_type = bot_type
        bot_class = BOT_CLASSES[bot_type]
        self.bot = bot_class(bot_id)

        self.backtest_lock = asyncio.Lock()
        self.train_lock = asyncio.Lock()

    async def start_bot(self, params=None):
        if params:
            self.bot.sync(params)
        self.bot.set_realtime_mode()
        await self.bot.start()
        self._logger.info(f"Bot {self.bot.bot_id} started")

    def stop_bot(self):
        self.bot.stop()
        self._logger.info(f"Bot {self.bot.bot_id} stopped")

    async def run_backtest(self, params):
        async with self.backtest_lock:
            bot_class = BOT_CLASSES[self.bot_type]
            backtest = Backtest(bot_class)
            stats, trades_list = await backtest.execute(params)
            return stats

    async def run_training(self, params_grid):
        async with self.train_lock:
            trainer = BotTrainer(BOT_CLASSES["sweep_bot"])
            summary_df, trades_list = await trainer.run(params_grid)
            top5 = (
                summary_df
                .sort_values(by="s_normalized_score", ascending=False)
                .head(5)
                .to_dict(orient="records")
            )
            return top5