from aiohttp import web

from trading_bot.core.logger import Logger

class HttpServerLogs():

    _logger = Logger.get("HttpServerLogs")

    async def execute(self, request):
        try:
            levels = Logger.get_all_levels()   # À ajouter dans ton Logger
            return web.json_response({"status": "ok", "levels": levels})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)