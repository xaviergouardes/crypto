import asyncio
import logging
from typing import Dict

from trading_bot.core.logger import Logger

from trading_bot.bots import BOT_CLASSES
from trading_bot.trainer.backtest import Backtest
from trading_bot.trainer.trainer import BotTrainer


class BotManager:
    """Gestion interne des bots, indépendante du serveur."""
    _logger = Logger.get("BotManager")

    def __init__(self):
        self.bots: Dict[str, object] = {}

    async def start_bot(self, name: str, bot_type: str, params: dict):
        if name in self.bots:
            return {"status": "error", "msg": f"{name} already running"}

        if bot_type not in BOT_CLASSES:
            return {"status": "error", "msg": f"Unknown bot_type {bot_type}"}

        bot_class = BOT_CLASSES[bot_type]
        bot = bot_class()
        bot.set_realtime_mode()
        bot.sync(params)

        # start async
        task = asyncio.create_task(bot.start())

        self.bots[name] = {"bot": bot, "task": task}
        return {"status": "ok", "msg": f"{name} started"}


    async def stop_bot(self, name: str):
        if name not in self.bots:
            return {"status": "error", "msg": f"{name} not found"}
        
        bot_entry = self.bots[name]
        bot = bot_entry["bot"]
        task = bot_entry["task"]

        bot.stop()

        # Wait for the task to finish or cancel
        try:
            await asyncio.wait_for(task, timeout=5)
        except asyncio.TimeoutError:
            task.cancel()
            self._logger.warning(f"{name} did not stop in time → canceled")

        del self.bots[name]
        return {"status": "ok", "msg": f"{name} stopped"}

    async def train_bot(self, bot_type: str, param_grid: dict):

        self.logger.info(f"Training sur {bot_type} demandé avec param_grid = {param_grid}")
        if bot_type not in BOT_CLASSES:
            return {"status": "error", "msg": f"Unknown bot_type {bot_type}"}

        bot_class = BOT_CLASSES[bot_type]
        trainer = BotTrainer(bot_class)
        summary_df, results = await trainer.run(param_grid)

        return {"status": "ok", "msg": "Trainning Terminé", "results": results}

    async def backtest_bot(self, bot_type: str, params: dict):
        self.logger.info(f"Backtest sur {bot_type} demandé avec params = {params}")
        if bot_type not in BOT_CLASSES:
            return {"status": "error", "msg": f"Unknown bot_type {bot_type}"}
        
        bot_class = BOT_CLASSES[bot_type]
        backtest_executor = Backtest(bot_class)
        stats, trades_list = await backtest_executor.execute(params)

        return {"status": "ok", "msg": "Backtest Terminé", "stats": stats}

    def list_bots(self):
        return {"status": "ok", "bots": list(self.bots.keys())}
