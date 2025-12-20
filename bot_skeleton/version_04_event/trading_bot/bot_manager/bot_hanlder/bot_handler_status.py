from aiohttp import web

from trading_bot.bot_manager.bot_controler import BotControler

class BotHandlerStatus():

    def __init__(self, bot_controler: BotControler):
        self.bot_controler = bot_controler

    async def execute(self, request):
        try:
            return web.json_response({
                "type": self.bot_controler.bot_type,
                "bot_id": self.bot_controler.bot.bot_id,  
                "running": "started" if self.bot_controler.bot.is_running() else "stopped",
                "uptime": str(self.bot_controler.bot.uptime),
                "candle_heartbeat": self.bot_controler.get_candle_heartbeat()
            },
            status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)