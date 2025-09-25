import asyncio
import os
from trading_bot.trading_bot_class import TradingBot

if __name__ == "__main__":
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    bot = TradingBot(api_key, api_secret)
    asyncio.run(bot.run())
