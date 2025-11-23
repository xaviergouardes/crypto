import json
import asyncio

from trading_bot.bot_manager.command_dispatcher import CommandDispatcher
from trading_bot.bot_manager.bot_manager import BotManager

class BotManagerServer:
    """Serveur TCP léger qui délègue la logique au Dispatcher."""

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
        print(f"BotManagerServer listening on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(BotManagerServer().run_server())
