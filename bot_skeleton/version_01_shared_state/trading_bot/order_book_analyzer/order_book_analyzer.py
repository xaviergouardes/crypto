import asyncio
from trading_bot.protocols.shared_state import SharedState
from trading_bot.protocols.protocols import OrderBookAnalyzerProtocol

class OrderBookAnalyzer(OrderBookAnalyzerProtocol):
    def __init__(self, shared_state):
        self.state = shared_state

    async def run(self):
        while True:
            order_book = await self.state.get("order_book")
            if order_book:
                support = max(order_book["bids"], key=lambda x: x[1])[0]
                resistance = max(order_book["asks"], key=lambda x: x[1])[0]
                await self.state.set("support", support)
                await self.state.set("resistance", resistance)
                print(f"[OrderBookAnalyzer] Support: {support} / Resistance: {resistance}")
            await asyncio.sleep(1)
