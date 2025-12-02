import argparse
import asyncio
import json
import logging
import aiohttp
from aiohttp import web

from trading_bot.bots import BOT_CLASSES
from trading_bot.core.logger import Logger
from trading_bot.trainer.backtest import Backtest
from trading_bot.trainer.trainer import BotTrainer

class HttpBotServer:
    """
    Serveur HTTP générique hébergé par un bot (hérite de BaseBot).
    """

    _logger = Logger.get("HttpBotServer")

    def __init__(self, bot_type, bot_id="bot_01", port=9101):

        self.bot_type = bot_type
        self.host = "127.0.0.1"
        self.port = port
        self.bot_manager_url = "http://127.0.0.1:9999/register"

        bot_class = BOT_CLASSES[bot_type]
        self.bot = bot_class(bot_id)

        self.app = web.Application()
        self.app.add_routes([
            web.post("/start", self._handle_start),
            web.post("/stop", self._handle_stop),
            web.post('/shutdown', self._handle_shutdown),
            web.post('/backtest', self._handle_backtest),
            web.post('/train', self._handle_train),
            web.get("/status", self._handle_status),
        ])

        self._runner = None
        self._site = None
        self._is_running = False
        self._shutdown_event = asyncio.Event()
        self.backtest_lock = asyncio.Lock()
        self.train_lock = asyncio.Lock()

    # ----------------------------
    # Endpoints
    # ----------------------------
    async def _handle_start(self, request):
        # await self.bot.start()
        return web.json_response({"status": "started", "bot_id": self.bot.bot_id})

    async def _handle_stop(self, request):
        # await self.bot.stop()
        return web.json_response({"status": "stopped", "bot_id": self.bot.bot_id})

    async def _handle_backtest(self, request):
        async with self.backtest_lock: # protection multi-requête
            try:
                data = await request.json()   # <--- Le body JSON
                params = data

                self._logger.info(f"[HTTP] Backtest demandé : bot={self.bot.bot_type}, params={params}")

                bot_class = BOT_CLASSES[self.bot.bot_type]
                backtest = Backtest(bot_class)
                stats, trades_list = await backtest.execute(params)

                return web.json_response({
                    "status": "ok",
                    "bot_id": self.bot.bot_id,
                    "bot_type": self.bot.bot_type,
                    "stats": stats
                })

            except Exception as e:
                self._logger.exception("Erreur dans _handle_backtest")
                return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def _handle_train(self, request):
        async with self.train_lock: # protection multi-requête
            try:
                data = await request.json()   # <--- Le body JSON
                params_grid = data

                self._logger.info(f"[HTTP] Training demandé : bot={self.bot.bot_type}, params={params_grid}")

                bot_class = BOT_CLASSES[self.bot.bot_type]
                trainer = BotTrainer(BOT_CLASSES["sweep_bot"])
                summary_df, trades_list = await trainer.run(params_grid)

                top5 = (
                    summary_df
                    .sort_values(by="s_normalized_score", ascending=False)
                    .head(5)
                    .to_dict(orient="records")
                )

                return web.json_response({
                    "status": "ok",
                    "bot_id": self.bot.bot_id,
                    "bot_type": self.bot.bot_type,
                    "stats": top5
                })

            except Exception as e:
                self._logger.exception("Erreur dans _handle_train")
                return web.json_response({"status": "error", "message": str(e)}, status=400)

    
    async def _handle_status(self, request):
        return web.json_response({
            "bot_id": self.bot.bot_id,
            "running": self.bot.is_running(),
            "type": self.bot.bot_type
        })
    
    async def _handle_shutdown(self, request):
        """Endpoint HTTP pour éteindre proprement le serveur."""
        self.bot.stop()
        asyncio.create_task(self.stop())   # ne bloque pas la requête
        return web.json_response({"status": "shutting_down"})
    
    # ----------------------------
    # Meta-server registration
    # ----------------------------
    async def register(self):
        """
        Enregistre le bot sur le BotManager.
        En cas d'échec, le bot continue à fonctionner de manière autonome.
        """
        payload = {
            "bot_id": self.bot.bot_id,
            "type": self.bot.bot_type,
            "host": self.host,
            "port": self.port,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.bot_manager_url, json=payload) as resp:
                    text = await resp.text()
                    self._logger.info(f"Enregistrement sur BotManager : {text}")

        except Exception as e:
            # Log et continue, le bot reste autonome
            self._logger.warning(f"⚠ Impossible de s’enregistrer sur BotManager")
            self._logger.debug(f"⚠ Impossible de s’enregistrer sur BotManager : {e}")



    # ---------- Server lifecycle ----------
    async def start(self):
        """Démarre le serveur HTTP non bloquant."""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()

        self._is_running = True
        self._logger.info(f"[HTTP] Bot HTTP server started on {self.host}:{self.port}")

    async def stop(self):
        """Stoppe proprement le serveur, le runner et débloque la boucle."""
        if not self._is_running:
            return

        self._logger.info("[HTTP] Shutting down HTTP server...")

        self._is_running = False

        # Arrête le site (listener TCP)
        if self._site:
            await self._site.stop()

        # Arrête l'app runner
        if self._runner:
            await self._runner.cleanup()

        # Permet au bot de terminer sa boucle
        self._shutdown_event.set()

        self._logger.info("[HTTP] HTTP server stopped")

    async def wait_closed(self):
        """Bloque jusqu'à ce que stop() soit appelé."""
        await self._shutdown_event.wait()



# ----------------------------------------
# Lancement direct
# ----------------------------------------
if __name__ == "__main__":
    Logger.set_default_level(logging.INFO)

    # Logger.set_level("BotManagerServer", logging.DEBUG)
    # Logger.set_level("CommandDispatcher", logging.DEBUG)
    # Logger.set_level("BotManager", logging.DEBUG)
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("Backtest", logging.DEBUG)
        
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot_type", default="bot_type")
    parser.add_argument("--bot_id", default="bot_01")
    parser.add_argument("--port", type=int, default=9101)
    args = parser.parse_args()

    # Création du bot avec paramètres dynamiques
    http_server = HttpBotServer(bot_type=args.bot_type, bot_id=args.bot_id, port=args.port)

    async def main():
        await http_server.start()
        await http_server.register()
        await http_server.wait_closed()

    asyncio.run(main())