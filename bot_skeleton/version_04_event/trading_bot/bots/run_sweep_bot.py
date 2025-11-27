import asyncio
import logging
from trading_bot.bots.sweep_bot import SweepBot
from trading_bot.core.logger import Logger

def main():
    params = {
        "symbol": "ethusdc",
        "interval": "1m",
        "initial_capital": 1000,
        "trading_system": {
            "swing_window": 21,
            "swing_side": 2,
            "tp_pct": 1.5,
            "sl_pct": 1.5
        }
    }

    bot = SweepBot()
    bot.sync(params)
    asyncio.run( bot.start() )
    print(" ============== Terminé ======================")

if __name__ == "__main__":
    # Niveau global : silence tout sauf WARNING et plus
    Logger.set_default_level(logging.INFO)

    # Niveau spécifique pour
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)

    main()

