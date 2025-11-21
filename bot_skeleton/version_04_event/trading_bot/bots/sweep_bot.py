
import asyncio
import logging
import pandas as pd
from itertools import product

from trading_bot.core.event_bus import EventBus

from trading_bot.core.logger import Logger

from trading_bot.engine.realtime_engine import RealTimeEngine
from trading_bot.engine.backtest_engine import BacktestEngine

from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

from trading_bot.trainer.trainer import BotTrainer

# Niveau global : silence tout sauf WARNING et plus
Logger.set_default_level(logging.INFO)

# Niveau spécifique pour SweepBot
Logger.set_level("PortfolioManager", logging.DEBUG)
Logger.set_level("TradeJournal", logging.DEBUG)

class SweepBot:

    logger = Logger.get("SweepBot")

    def __init__(self, params, mode):

        self.event_bus = EventBus()
        
        self.params = params
        self.system_trading = SimpleSweepSystemTrading(self.event_bus, params)   

        if mode == "backtest":
            self.engine = BacktestEngine(self.event_bus, self.system_trading, self.params)
        else:
            self.engine = RealTimeEngine(self.event_bus, self.system_trading, self.params)

    async def run(self):
        stats = await self.engine.run()
        self.logger.info(f"Statistiques : {stats}")
        return stats

    async def train(self):

        param_grid = {
            "swing_window": [21, 50, 75, 100, 150 , 200],
            "tp_pct": [1.0, 1.5, 2, 2.5, 3, 3.5],
            "sl_pct": [0.5, 1, 1.5, 2, 2.5]
        }
        self.params["warmup_count"] = max(param_grid["swing_window"])

        trainer = BotTrainer(SweepBot, self.params)
        best_params = await trainer.run(param_grid)

        self.logger.info(f"Best param : \n {best_params}")

if __name__ == "__main__":

    # Lancer le bot en mode backtest
    params = {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "5m",
        # "warmup_count": 200,
        "initial_capital": 1000,
        "ema_fast": 7,
        "ema_slow": 21,
        "swing_window": 50,
        "swing_side": 2,
        "tp_pct": 1,
        "sl_pct": 2.5
    }

    bot = SweepBot(params, "backtest")
    # asyncio.run(bot.train())
    asyncio.run(bot.run())

    # params = {
    #     "symbol": "ethusdc",
    #     "interval": "1m",
    #     "warmup_count": 3,
    #     "initial_capital": 1000,
    #     "tp_pct": 0.1,
    #     "sl_pct": 0.05
    # }

    # params = {
    #     "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
    #     "symbol": "ethusdc",
    #     "interval": "1m",
    #     "warmup_count": 21,
    #     "initial_capital": 1000,
    #     "ema_fast": 7,
    #     "ema_slow": 21,
    #     "swing_window": 21,
    #     "swing_side": 2,
    #     "tp_pct": 1.6,
    #     "sl_pct": 1
    # }

    # bot = TradingBot(params, "realtime")
    # asyncio.run(bot.run())

    print("\n=== ✅ Bot terminé ===\n")