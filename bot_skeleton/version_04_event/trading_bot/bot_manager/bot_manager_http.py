import asyncio
import logging
from aiohttp import web
import aiohttp

from trading_bot.core.logger import Logger


class BotManagerHttp:

    logger = Logger.get("BotManagerHttp")

    def __init__(self, host="127.0.0.1", port=9999):
        self.host = host
        self.port = port
        self.bots = {}          # registry: bot_id -> {host, port, type}
        self.app = web.Application()
        self._setup_routes()

    # ----------------------------
    # Routes setup
    # ----------------------------
    def _setup_routes(self):
        self.app.add_routes([
            web.post('/register', self.register),
            web.get('/list', self.list_bots), 
            web.post('/bots/{bot_id}/start', self.handle_start),
            web.post('/bots/{bot_id}/stop', self.handle_stop),
        ])

    # ----------------------------
    # Endpoints
    # ----------------------------
    async def list_bots(self, request):
        """Retourne la liste complète des bots avec leurs attributs."""
        result = []

        for bot_id, bot_data in self.bots.items():
            entry = {
                "bot_id": bot_id,
                "host": bot_data.get("host"),
                "port": bot_data.get("port"),
            }
            result.append(entry)

        self.logger.debug(f"[BotManagerHttp] /list => {result}")
        return web.json_response({"bots": result})
    

    async def register(self, request):
        data = await request.json()
        bot_id = data["bot_id"]
        self.bots[bot_id] = data
        self.logger.info(f"[BotManagerHttp] Bot enregistré : {bot_id} -> {data}")
        return web.json_response({"status": "ok"})

    async def handle_start(self, request):
        bot_id = request.match_info["bot_id"]
        self.logger.debug(f"Start demandé pour {bot_id}")
        return await self._proxy_to_bot(bot_id, "/start", request)

    async def handle_stop(self, request):
        bot_id = request.match_info["bot_id"]
        self.logger.debug(f"Stop demandé pour {bot_id}")
        return await self._proxy_to_bot(bot_id, "/stop", request)

    # ----------------------------
    # Proxy logic
    # ----------------------------
    async def _proxy_to_bot(self, bot_id, path, request):
        if bot_id not in self.bots:
            return web.json_response({"error": "bot not found"}, status=404)

        bot = self.bots[bot_id]
        url = f"http://{bot['host']}:{bot['port']}{path}"

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=url,
                json=await request.json() if request.can_read_body else None
            ) as resp:

                try:
                    data = await resp.json()
                except:
                    data = await resp.text()

                return web.json_response(data, status=resp.status)

    # ----------------------------
    # Start server
    # ----------------------------
    def start(self):
        self.logger.info(f"[BotManagerHttp] Démarrage sur {self.host}:{self.port}")
        web.run_app(self.app, host=self.host, port=self.port)


# ----------------------------------------
# Lancement direct
# ----------------------------------------
if __name__ == "__main__":
    Logger.set_default_level(logging.DEBUG)

    # Logger.set_level("BotManagerServer", logging.DEBUG)
    # Logger.set_level("CommandDispatcher", logging.DEBUG)
    # Logger.set_level("BotManager", logging.DEBUG)
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("Backtest", logging.INFO)
    server = BotManagerHttp()
    server.start()
