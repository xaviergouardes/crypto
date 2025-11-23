import asyncio
from trading_bot.bots.sweep_bot import SweepBot

async def main():
    params = {
        "symbol": "ethusdc",
        "interval": "1m",
        "initial_capital": 1000,
        "swing_window": 21,
        "swing_side": 2,
        "tp_pct": 1.5,
        "sl_pct": 1.5
    }

    bot = SweepBot(params)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())

