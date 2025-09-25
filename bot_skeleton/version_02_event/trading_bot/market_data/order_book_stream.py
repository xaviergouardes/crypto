import asyncio
import aiohttp
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import OrderBookUpdated

class OrderBookStream:
    """Carnet d'ordre Binance Spot 1000 niveaux avec snapshot REST + updates WebSocket."""

    def __init__(self, event_bus: EventBus, symbol: str = "ethusdt"):
        self.event_bus = event_bus
        self.symbol = symbol.lower()
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@depth10@100ms"
        self.rest_url = f"https://api.binance.com/api/v3/depth?symbol={self.symbol.upper()}&limit=1000"
        self.bids = {}
        self.asks = {}

    async def fetch_snapshot(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.rest_url) as resp:
                data = await resp.json()
                self.bids = {float(p): float(q) for p, q in data.get("bids", [])}
                self.asks = {float(p): float(q) for p, q in data.get("asks", [])}
                print(f"[OrderBookStream] Snapshot reçu: {len(self.bids)} bids / {len(self.asks)} asks")
                await self.event_bus.publish(OrderBookUpdated(
                    symbol=self.symbol.upper(),
                    bids=sorted(self.bids.items(), reverse=True),
                    asks=sorted(self.asks.items())
                ))

    def apply_update(self, update: dict):
        # Bids
        for price, qty in update.get("bids", []):
            price, qty = float(price), float(qty)
            if qty == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = qty

        # Asks
        for price, qty in update.get("asks", []):
            price, qty = float(price), float(qty)
            if qty == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = qty

        # Limiter à 1000 niveaux
        self.bids = dict(sorted(self.bids.items(), reverse=True)[:1000])
        self.asks = dict(sorted(self.asks.items())[:1000])

    async def run(self):
        await self.fetch_snapshot()

        while True:
            try:
                print(f"[OrderBookStream] Connexion WebSocket pour {self.symbol.upper()}...")
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self.ws_url) as ws:
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = msg.json()
                                self.apply_update(data)
                                await self.event_bus.publish(OrderBookUpdated(
                                    symbol=self.symbol.upper(),
                                    bids=sorted(self.bids.items(), reverse=True),
                                    asks=sorted(self.asks.items())
                                ))
                                # print(f"[OrderBookStream] Update appliqué: {len(self.bids)} bids / {len(self.asks)} asks")

                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                print("[OrderBookStream] Erreur WebSocket, reconnexion dans 5s...")
                                break

            except Exception as e:
                print(f"[OrderBookStream] Exception: {e}, reconnexion dans 5s...")

            await asyncio.sleep(5)
