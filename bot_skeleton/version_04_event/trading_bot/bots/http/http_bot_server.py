import asyncio
import aiohttp
from aiohttp import web

from trading_bot.core.logger import Logger
from trading_bot.trainer.backtest import Backtest

class HttpBotServer:
    """
    Serveur HTTP générique hébergé par un bot (hérite de BaseBot).
    """

    _logger = Logger.get("HttpBotServer")

    def __init__(self, bot, port=9101):

        self.bot = bot
        self.host = "127.0.0.1"
        self.port = port
        self.bot_manager_url = "http://127.0.0.1:9999/register"

        self.app = web.Application()
        self.app.add_routes([
            web.post("/start", self._handle_start),
            web.post("/stop", self._handle_stop),
            web.get("/status", self._handle_status),
            web.post('/shutdown', self._handle_shutdown),
            web.post('/backtest', self._handle_backtest),
        ])

        self._runner = None
        self._site = None
        self._is_running = False
        self._shutdown_event = asyncio.Event()

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
        try:
            data = await request.json()   # <--- Le body JSON

            # Exemple d'accès aux champs
            params = data

            # Log pour debug
            self._logger.info(f"[HTTP] Backtest demandé : bot={self.bot.bot_type}, params={params}")

            bot_class = self.bot.__class__
            backtest_executor = Backtest(bot_class)
            stats, trades_list = await backtest_executor.execute(params)

            return web.json_response({
                "status": "ok",
                "bot_id": self.bot.bot_id,
                "bot_type": self.bot.bot_type,
                "stats": stats
            })

        except Exception as e:
            self._logger.exception("Erreur dans _handle_backtest")
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    
    async def _handle_status(self, request):
        return web.json_response({
            "bot_id": self.bot.bot_id,
            "running": self.bot.is_running(),
            "type": self.bot.bot_type
        })
    
    async def _handle_shutdown(self, request):
        """Endpoint HTTP pour éteindre proprement le serveur."""
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
