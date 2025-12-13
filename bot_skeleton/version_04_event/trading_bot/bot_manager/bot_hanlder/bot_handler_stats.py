from aiohttp import web

from trading_bot.bot_manager.bot_controler import BotControler

class BotHandlerStats():

    def __init__(self, bot_controler: BotControler):
        self.bot_controler = bot_controler

    async def execute(self, request):
        try:
            stats = self.bot_controler.get_stats()
            return web.json_response({
                "bot_id": self.bot_controler.bot.bot_id,
                "type": self.bot_controler.bot_type,
                "uptime": str(self.bot_controler.bot.uptime),
                "stats": stats
            },
            status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)