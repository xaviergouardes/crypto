import json
import asyncio
import logging

from trading_bot.bot_manager.command_dispatcher import CommandDispatcher
from trading_bot.bot_manager.bot_manager import BotManager
from trading_bot.core.logger import Logger

class BotManagerServer:
    """Serveur TCP léger qui délègue la logique au Dispatcher."""
    _logger = Logger.get("BotManagerServer")

    def __init__(self, host="127.0.0.1", port=9999):
        self.host = host
        self.port = port
        self.manager = BotManager()
        self.dispatcher = CommandDispatcher(self.manager)

    async def handle_client(self, reader, writer):
        try:
            while data := await reader.read(65536):
                msg = json.loads(data.decode())
                response = await self.dispatcher.dispatch(msg)
                writer.write(json.dumps(response).encode())
                await writer.drain()
        except Exception as e:
            writer.write(json.dumps({"error": str(e)}).encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def run_server(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        self._logger.info(f"BotManagerServer listening on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":

    Logger.set_default_level(logging.INFO)

    # Logger.set_level("BotManagerServer", logging.DEBUG)
    # Logger.set_level("CommandDispatcher", logging.DEBUG)
    # Logger.set_level("BotManager", logging.DEBUG)
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("Backtest", logging.INFO)

    asyncio.run(BotManagerServer().run_server())
