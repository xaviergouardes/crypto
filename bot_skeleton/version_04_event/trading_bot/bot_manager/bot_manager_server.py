import asyncio
import json
from typing import Dict
import logging

from trading_bot.core.logger import Logger

from trading_bot.bots import BOT_CLASSES


# Niveau global : silence tout sauf WARNING et plus
Logger.set_default_level(logging.INFO)

# Niveau spécifique pour
# Logger.set_level("BotTrainer", logging.INFO)
# Logger.set_level("PortfolioManager", logging.DEBUG)
# Logger.set_level("TradeJournal", logging.DEBUG)

class BotManagerServer:
    """
    Serveur capable de piloter plusieurs types de bots.
    """

    def __init__(self, host="127.0.0.1", port=9999):
        self.host = host
        self.port = port
        self.bots: Dict[str, object] = {}  # nom -> instance du bot

    async def handle_client(self, reader, writer):
        while True:
            try:
                data = await reader.read(65536)
                if not data:
                    break
                message = json.loads(data.decode())
                response = await self.process_command(message)
                writer.write(json.dumps(response).encode())
                await writer.drain()
            except Exception as e:
                writer.write(json.dumps({"error": str(e)}).encode())
                await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def process_command(self, message: dict):
        cmd = message.get("command")
        bot_name = message.get("bot_name")
        bot_type = message.get("bot_type", "sweep")
        params = message.get("params", {})

        if cmd == "start_bot":
            if bot_name in self.bots:
                return {"status": "error", "msg": f"{bot_name} already running"}
            if bot_type not in BOT_CLASSES:
                return {"status": "error", "msg": f"Unknown bot_type {bot_type}"}
            bot_class = BOT_CLASSES[bot_type]
            bot = bot_class(params, "backtest")
            self.bots[bot_name] = bot
            asyncio.create_task(bot.run())  # lance le bot en tâche asynchrone
            return {"status": "ok", "msg": f"{bot_name} started as {bot_type}"}

        elif cmd == "stop_bot":
            if bot_name in self.bots:
                # à adapter selon méthode stop() du bot
                del self.bots[bot_name]
                return {"status": "ok", "msg": f"{bot_name} stopped"}
            return {"status": "error", "msg": f"{bot_name} not found"}

        elif cmd == "train_bot":
            if bot_name in self.bots:
                bot = self.bots[bot_name]
                summary, results = await bot.train()
                return {"status": "ok", "summary": summary.to_dict(), "results": results}
            return {"status": "error", "msg": f"{bot_name} not found"}


        elif cmd == "backtest_bot":
            if bot_name in self.bots:
                bot = self.bots[bot_name]
                stats = await bot.backtest()
                return {"status": "ok", "stats": stats}
            return {"status": "error", "msg": f"{bot_name} not found"}


        elif cmd == "list_bots":
            return {"status": "ok", "bots": list(self.bots.keys())}
        
        else:
            return {"status": "error", "msg": "Unknown command"}

    async def run_server(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"BotManagerServer listening on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()

# Exécution
if __name__ == "__main__":
    server = BotManagerServer()
    asyncio.run(server.run_server())
