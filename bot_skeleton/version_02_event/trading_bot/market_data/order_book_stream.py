# trading_bot/market_data/order_book_stream.py
import asyncio
import aiohttp
from core.event_bus import EventBus
from core.events import OrderBookUpdated

class OrderBookStream:
    def __init__(self, event_bus: EventBus, symbol: str = "ethusdc"):
        self.event_bus = event_bus
        self.symbol = symbol.lower()
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@depth5@100ms"

    async def run(self):
        print(f"[OrderBookStream] Connexion WebSocket pour {self.symbol.upper()}...")
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.ws_url) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = msg.json()
                        bids = [(float(price), float(qty)) for price, qty in data["b"]]
                        asks = [(float(price), float(qty)) for price, qty in data["a"]]
                        await self.event_bus.publish(OrderBookUpdated(
                            symbol=self.symbol.upper(),
                            bids=bids,
                            asks=asks
                        ))
                        print(f"[OrderBookStream] Carnet reçu: {len(bids)} bids / {len(asks)} asks")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print("[OrderBookStream] Erreur WebSocket, reconnexion dans 5s...")
                        await asyncio.sleep(5)
                        return await self.run()
