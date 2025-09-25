import asyncio
from binance import BinanceSocketManager

from trading_bot.protocols.shared_state import SharedState
from trading_bot.protocols.protocols import OrderBookDataProtocol

class OrderBookData(OrderBookDataProtocol):
    def __init__(self, shared_state, client, symbol="BTCUSDT", depth=5):
        self.state = shared_state
        self.client = client
        self.symbol = symbol
        self.depth = depth

    async def run(self):
        bsm = BinanceSocketManager(self.client)
        async with bsm.depth_socket(self.symbol, depth=self.depth) as stream:
            while True:
                msg = await stream.recv()

                # Vérification des clés
                bids_data = msg.get('b') or msg.get('bids')
                asks_data = msg.get('a') or msg.get('asks')

                if bids_data and asks_data:
                    bids = [(float(price), float(qty)) for price, qty in bids_data]
                    asks = [(float(price), float(qty)) for price, qty in asks_data]
                    await self.state.set("order_book", {"bids": bids, "asks": asks})
                    print(f"[OrderBookData] Carnet mis à jour")
                else:
                    print(f"[OrderBookData] Message inattendu : {msg}")

                await asyncio.sleep(0.1)
