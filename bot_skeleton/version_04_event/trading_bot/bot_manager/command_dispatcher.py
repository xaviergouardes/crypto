from trading_bot.bot_manager.bot_manager import BotManager
from trading_bot.core.logger import Logger

class CommandDispatcher:
    """Mappe un message JSON à une méthode du BotManager."""
    _logger = Logger.get("CommandDispatcher")

    def __init__(self, manager: BotManager):
        self.manager = manager
        self.commands = {
            "start_bot": self._start,
            "stop_bot": self._stop,
            "train_bot": self._train,
            "backtest_bot": self._backtest,
            "list_bots": self._list,
        }

    async def dispatch(self, message: dict):
        cmd = message.get("command")
        handler = self.commands.get(cmd)

        if not handler:
            return {"status": "error", "msg": "Unknown command"}

        return await handler(message)

    async def _start(self, msg):
        return await self.manager.start_bot(
            msg["bot_name"],
            msg.get("bot_type", "sweep"),
            msg.get("params", {})
        )

    async def _stop(self, msg):
        return await self.manager.stop_bot(msg["bot_name"])

    async def _train(self, msg):
        self._logger.debug(f"Commande à dispatcher {msg}")
        return await self.manager.train_bot(
            msg.get("bot_type", None),
            msg.get("param_grid", None)
        )

    async def _backtest(self, msg):
        self._logger.debug(f"Commande à dispatcher {msg}")
        return await self.manager.backtest_bot(
            msg.get("bot_type", None),
            msg.get("params", None)
        )

    async def _list(self, msg):
        return self.manager.list_bots()
