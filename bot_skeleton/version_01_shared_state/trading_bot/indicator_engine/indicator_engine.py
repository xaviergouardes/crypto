import asyncio
from trading_bot.protocols.shared_state import SharedState
from trading_bot.protocols.protocols import IndicatorEngineProtocol

class IndicatorEngine(IndicatorEngineProtocol):
    def __init__(self, shared_state):
        self.state = shared_state

    async def run(self):
        while True:
            price = await self.state.get("price")
            if price:
                indicator = price * 0.99  # simulation
                await self.state.set("indicator", indicator)
            await asyncio.sleep(1)
