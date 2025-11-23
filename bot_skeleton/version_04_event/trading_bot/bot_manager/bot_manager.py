import asyncio
from typing import Dict
from trading_bot.bots import BOT_CLASSES

class BotManager:
    """Gestion interne des bots, indépendante du serveur."""
    
    def __init__(self):
        self.bots: Dict[str, object] = {}

    async def start_bot(self, name: str, bot_type: str, params: dict):
        if name in self.bots:
            return {"status": "error", "msg": f"{name} already running"}

        if bot_type not in BOT_CLASSES:
            return {"status": "error", "msg": f"Unknown bot_type {bot_type}"}

        bot_class = BOT_CLASSES[bot_type]
        bot = bot_class(params, "backtest")

        self.bots[name] = bot
        asyncio.create_task(bot.run())

        return {"status": "ok", "msg": f"{name} started"}

    async def stop_bot(self, name: str):
        if name not in self.bots:
            return {"status": "error", "msg": f"{name} not found"}

        del self.bots[name]
        return {"status": "ok", "msg": f"{name} stopped"}

    async def train_bot(self, name: str):
        if name not in self.bots:
            return {"status": "error", "msg": f"{name} not found"}

        summary, results = await self.bots[name].train()
        return {"status": "ok", "summary": summary.to_dict(), "results": results}

    async def backtest_bot(self, name: str):
        if name not in self.bots:
            return {"status": "error", "msg": f"{name} not found"}

        stats = await self.bots[name].backtest()
        return {"status": "ok", "stats": stats}

    def list_bots(self):
        return {"status": "ok", "bots": list(self.bots.keys())}
