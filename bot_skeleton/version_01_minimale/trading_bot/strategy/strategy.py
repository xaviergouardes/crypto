import asyncio
from trading_bot.protocols.shared_state import SharedState
from trading_bot.protocols.protocols import StrategyProtocol

class Strategy(StrategyProtocol):
    def __init__(self, shared_state):
        self.state = shared_state

    async def run(self):
        while True:
            indicator = await self.state.get("indicator")
            support = await self.state.get("support")
            resistance = await self.state.get("resistance")
            if indicator and support and resistance:
                signal = "BUY" if indicator < support else "SELL" if indicator > resistance else "HOLD"
                await self.state.set("signal", signal)
                print(f"[Strategy] Signal: {signal}")
            await asyncio.sleep(1)
