# trading_bot/market_data/price_stream.py
import os
import asyncio
import aiohttp
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import PriceUpdated

class PriceStream:
    def __init__(self, event_bus: EventBus, symbol: str = "ethusdc"):
        self.event_bus = event_bus
        self.symbol = symbol.lower()
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@trade"

    async def run(self):
        print(f"[PriceStream] Connexion WebSocket pour {self.symbol.upper()}...")
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.ws_url) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = msg.json()
                        price = float(data["p"])  # prix de la transaction
                        await self.event_bus.publish(PriceUpdated(symbol=self.symbol.upper(), price=price))
                        # print(f"[PriceStream] Nouveau prix: {price}")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print("[PriceStream] Erreur WebSocket, reconnexion dans 5s...")
                        await asyncio.sleep(5)
                        return await self.run()
