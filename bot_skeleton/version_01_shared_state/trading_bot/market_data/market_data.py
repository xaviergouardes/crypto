from binance import BinanceSocketManager
import asyncio
from trading_bot.protocols.shared_state import SharedState
from trading_bot.protocols.protocols import MarketDataProtocol

class MarketData(MarketDataProtocol):
    def __init__(self, shared_state, client, symbol="BTCUSDT"):
        self.state = shared_state
        self.client = client
        self.symbol = symbol

    async def run(self):
        bsm = BinanceSocketManager(self.client)
        async with bsm.symbol_ticker_socket(self.symbol) as stream:
            while True:
                msg = await stream.recv()
                price = float(msg['c'])
                await self.state.set("price", price)
                print(f"[MarketData] Prix: {price}")