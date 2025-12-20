import argparse
import asyncio
import logging

import aiohttp
from aiohttp import web

from trading_bot.bot_manager.bot_hanlder.bot_handler_backtest import BotHandlerBacktest
from trading_bot.bot_manager.bot_hanlder.bot_handler_start import BotHandlerStart
from trading_bot.bot_manager.bot_hanlder.bot_handler_stats import BotHandlerStats
from trading_bot.bot_manager.bot_hanlder.bot_handler_status import BotHandlerStatus
from trading_bot.bot_manager.bot_hanlder.bot_handler_stop import BotHandlerStop
from trading_bot.bot_manager.bot_hanlder.bot_handler_train import BotHandlerTrain
from trading_bot.bot_manager.bot_hanlder.server_http_handler_change_logs import HttpServerChangeLogs
from trading_bot.bot_manager.bot_hanlder.server_http_handler_logs import HttpServerLogs
from trading_bot.core.logger import Logger
from trading_bot.bot_manager.bot_controler import BotControler

class HttpBotServer:
    _logger = Logger.get("HttpBotServer")

    def __init__(self, bot_controler: BotControler, host="127.0.0.1", port=9101):
        self.bot_controler = bot_controler
        self.host = host
        self.port = port

        self.app = web.Application()
        self.app.add_routes([
            web.post("/server/shutdown", self._handle_shutdown),
            web.get("/server/status", self._handle_status),
            web.post("/server/log-level", HttpServerChangeLogs().execute),
            web.get("/server/log-level", HttpServerLogs().execute),
        ])

        self.app.add_routes([
            web.post("/bot/start", BotHandlerStart(self.bot_controler).execute),
            web.post("/bot/stop", BotHandlerStop(self.bot_controler).execute),
            web.post("/bot/backtest", BotHandlerBacktest(self.bot_controler).execute),
            web.post("/bot/train", BotHandlerTrain(self.bot_controler).execute),
            web.get("/bot/status", BotHandlerStatus(self.bot_controler).execute),
            web.get("/bot/stats", BotHandlerStats(self.bot_controler).execute),
        ])

        self._runner = None
        self._site = None
        self._is_running = False
        self._shutdown_event = asyncio.Event()

    async def _handle_shutdown(self, request):
        try:
            """Arrête le bot et le serveur HTTP proprement."""
            self._logger.info(f"Shutdown requested for bot {self.bot_controler.bot.bot_id}")
            self.bot_controler.stop_bot()
            # Lance le shutdown du serveur en tâche de fond pour ne pas bloquer la requête
            asyncio.create_task(self.stop())
            return web.json_response({"status": "server_shutting_down", "bot_id": self.bot_controler.bot.bot_id}, status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_status(self, request):
        try:
            return web.json_response({
                "server": "started" if self._is_running else "stopped",
                "bot_id": self.bot_controler.bot.bot_id,
                "type": self.bot_controler.bot_type
            },
            status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
        

    # ----------------------------
    # Server lifecycle
    # ----------------------------
    async def start(self):
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()
        self._is_running = True
        self._logger.info(f"HTTP server started on {self.host}:{self.port}")

    async def stop(self):
        if not self._is_running:
            return
        self._logger.info("Shutting down HTTP server...")
        self._is_running = False
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        self._shutdown_event.set()
        self._logger.info("HTTP server stopped")

    async def wait_closed(self):
        await self._shutdown_event.wait()

# ----------------------------
# Lancement direct
# ----------------------------
if __name__ == "__main__":
    Logger.set_default_level(logging.DEBUG)
    Logger.set_level("TradeJournal", logging.INFO)
    # Logger.set_level("TradeJournal", logging.WARN)

    parser = argparse.ArgumentParser()
    parser.add_argument("--bot_type", default="sweep_bot")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9101)
    args = parser.parse_args()

    bot_id = f"{args.bot_type}_{args.port}"
    bot_controler = BotControler(bot_type=args.bot_type, bot_id=bot_id)
    http_server = HttpBotServer(bot_controler=bot_controler, host=args.host ,port=args.port)

    async def main():
        # Optionnel : enregistrement auprès du BotManager
        try:
            payload = {
                "bot_id": bot_controler.bot_id,
                "type": bot_controler.bot_type,
                "host": http_server.host,
                "port": http_server.port,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post("http://127.0.0.1:9999/register", json=payload) as resp:
                    text = await resp.text()
                    Logger.get("HttpBotServer").info(f"Registered on BotManager: {text}")
        except Exception as e:
            Logger.get("HttpBotServer").warning(f"⚠ Failed to register on BotManager: {e}")
            
        await http_server.start()
        await http_server.wait_closed()

    asyncio.run(main())