import argparse
import asyncio
import logging

import aiohttp
from aiohttp import web

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
            web.post("/start", self._handle_start),
            web.post("/stop", self._handle_stop),
            web.post("/shutdown", self._handle_shutdown),
            web.post("/backtest", self._handle_backtest),
            web.post("/train", self._handle_train),
            web.get("/status", self._handle_status),
            web.get("/stats", self._handle_stats),
            web.get("/log-level", self._handle_get_log_level),
            # web.post("/log-level", self._handle_set_log_level),
        ])

        self._runner = None
        self._site = None
        self._is_running = False
        self._shutdown_event = asyncio.Event()

    async def _handle_get_log_level(self, request):
        try:
            levels = Logger.get_all_levels()   # À ajouter dans ton Logger
            return web.json_response({"status": "ok", "levels": levels})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)


    # async def _handle_set_log_level(self, request):
    #     try:
    #         data = await request.json()

    #         logger_name = data.get("logger")      # ex: "Backtest", "TradeJournal", "Bot.sweep_bot_01"
    #         level       = data.get("level")       # ex: "DEBUG", "INFO", "WARN", "ERROR"

    #         if not logger_name or not level:
    #             return web.json_response(
    #                 {"error": "Fields 'logger' and 'level' are required"},
    #                 status=400
    #             )

    #         ok = Logger.set_level(logger_name, level)

    #         if not ok:
    #             return web.json_response({"error": "Unknown logger or invalid level"}, status=404)

    #         return web.json_response({
    #             "status": "ok",
    #             "logger": logger_name,
    #             "new_level": level
    #         })

    #     except Exception as e:
    #         return web.json_response({"error": str(e)}, status=500)


    async def _handle_start(self, request):
        try:
            data = await request.json()
            await self.bot_controler.start_bot(data)       
            return web.json_response({"status": "started", "bot_id": self.bot_controler.bot.bot_id}, status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_stop(self, request):
        try:
            self.bot_controler.stop_bot()
            return web.json_response({"status": "stopped", "bot_id": self.bot_controler.bot.bot_id}, status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

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

    async def _handle_backtest(self, request):
        try:
            data = await request.json()
            stats = await self.bot_controler.run_backtest(data)
            return web.json_response({
                "status": "ok",
                "bot_id": self.bot_controler.bot.bot_id,
                "stats": stats
            },
            status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_train(self, request):
        try:
            data = await request.json()
            top5 = await self.bot_controler.run_training(data)
            return web.json_response({
                "status": "ok",
                "bot_id": self.bot_controler.bot.bot_id,
                "stats": top5
            },
            status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_status(self, request):
        try:
            return web.json_response({
                "bot_id": self.bot_controler.bot.bot_id,
                "running": self.bot_controler.bot.is_running(),
                "type": self.bot_controler.bot_type
            },
            status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_stats(self, request):
        try:
            stats = self.bot_controler.get_stats()
            return web.json_response({
                "bot_id": self.bot_controler.bot.bot_id,
                "type": self.bot_controler.bot_type,
                "stats": stats
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
    # parser.add_argument("--bot_id", default="bot_id")
    parser.add_argument("--port", type=int, default=9101)
    args = parser.parse_args()

    bot_id = f"{args.bot_type}_{args.port}"
    bot_controler = BotControler(bot_type=args.bot_type, bot_id=bot_id)
    http_server = HttpBotServer(bot_controler=bot_controler, port=args.port)

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