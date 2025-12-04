import asyncio
import logging
from trading_bot.bots.sweep_bot import SweepBot
from trading_bot.bots.random_bot import RandomBot
from trading_bot.core.logger import Logger

async def main():
    # params = {
    #     "symbol": "ethusdc",
    #     "interval": "1m",
    #     "initial_capital": 1000,
    #     "trading_system": {
    #         "swing_window": 21,
    #         "swing_side": 2,
    #         "tp_pct": 1.5,
    #         "sl_pct": 1.5
    #     }
    # }

    params = {
    "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
    "symbol": "ethusdc",
    "interval": "1m",
    "initial_capital": 1000,
    "trading_system": {
        "warmup_count": 5,
        "initial_capital": 1000,
        "tp_pct": 0.05,
        "sl_pct": 0.025
    }
    }

    # bot = SweepBot()
    bot = Ran
    bot.sync(params)
    bot.set_realtime_mode()

    try:
        print("====> 1 Bot lancé, attente 3 minutes...")
        await bot.start()
        await asyncio.sleep(70)  # 3 minutes
        bot.stop()

        await asyncio.sleep(120)  # 3 minutes

        print("====> 2 Bot lancé, attente 3 minutes...")
        await bot.start()
        await asyncio.sleep(70)  # 3 minutes
        bot.stop()

    except Exception as e:
        print(f"Erreur pendant l'exécution : {e}")

    finally:
        print("Arrêt du bot...")
        bot.stop()
        print("Bot arrêté proprement.")
        
    print(" ============== Terminé ======================")

if __name__ == "__main__":
    # Niveau global : silence tout sauf WARNING et plus
    Logger.set_default_level(logging.INFO)

    # Niveau spécifique pour
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)

    asyncio.run(main())

