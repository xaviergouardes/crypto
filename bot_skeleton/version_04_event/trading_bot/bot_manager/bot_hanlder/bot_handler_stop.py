from aiohttp import web

from trading_bot.bot_manager.bot_controler import BotControler

class BotHandlerStop():

    def __init__(self, bot_controler: BotControler):
        self.bot_controler = bot_controler

    async def execute(self, request):
        try:
            self.bot_controler.stop_bot()
            return web.json_response({"status": "stopped", "bot_id": self.bot_controler.bot.bot_id}, status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)