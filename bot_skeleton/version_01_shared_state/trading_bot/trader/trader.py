import asyncio
from trading_bot.protocols.shared_state import SharedState
from trading_bot.protocols.protocols import TraderProtocol

class Trader:
    def __init__(self, shared_state):
        self.state = shared_state

    async def run(self):
        while True:
            signal = await self.state.get("signal")
            risk_ok = await self.state.get("risk_ok")
            if signal and risk_ok and signal != "HOLD":
                print(f"[Trader] Exécution simulée de l'ordre: {signal}")
            await asyncio.sleep(1)
