from aiohttp import web

from trading_bot.bot_manager.bot_controler import BotControler

class BotHandlerStart():

    def __init__(self, bot_controler: BotControler):
        self.bot_controler = bot_controler

    async def execute(self, request):
        try:
            data = await request.json()
            await self.bot_controler.start_bot(data)       
            return web.json_response({"status": "started", "bot_id": self.bot_controler.bot.bot_id}, status=200)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)