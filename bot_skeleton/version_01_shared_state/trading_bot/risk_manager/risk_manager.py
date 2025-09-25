import asyncio
from trading_bot.protocols.shared_state import SharedState
from trading_bot.protocols.protocols import RiskManagerProtocol

class RiskManager(RiskManagerProtocol):
    def __init__(self, shared_state):
        self.state = shared_state

    async def run(self):
        while True:
            signal = await self.state.get("signal")
            if signal:
                risk_ok = True
                await self.state.set("risk_ok", risk_ok)
            await asyncio.sleep(1)
