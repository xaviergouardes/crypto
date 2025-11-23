
import asyncio
import logging

from trading_bot.core.logger import Logger

from trading_bot.core.event_bus import EventBus

from trading_bot.engine.realtime_engine import RealTimeEngine
from trading_bot.engine.backtest_engine import BacktestEngine

from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

from trading_bot.trainer.trainer import BotTrainer

# Niveau global : silence tout sauf WARNING et plus
Logger.set_default_level(logging.ERROR)

# Niveau spécifique pour
# Logger.set_level("BotTrainer", logging.INFO)
# Logger.set_level("PortfolioManager", logging.DEBUG)
# Logger.set_level("TradeJournal", logging.DEBUG)

class SweepBot:

    logger = Logger.get("SweepBot")

    def __init__(self, params, mode):

        self.event_bus = EventBus()
        self.system_trading = SimpleSweepSystemTrading(self.event_bus, params)   
        self.params = params

        if mode == "backtest":
            self.engine = BacktestEngine(self.event_bus, self.system_trading, self.params)
        else:
            self.engine = RealTimeEngine(self.event_bus, self.system_trading, self.params)

        self.logger.info(f"Bot {self.__class__.__name__} Initilisation Terminée mode={mode}")

    async def run(self):
        stats = await self.engine.run()
        self.logger.info(f"Statistiques : {stats}")
        return stats
    
    async def backtest(self):
        self.engine = BacktestEngine(self.event_bus, self.system_trading, self.params)
        stats = await self.engine.run()
        self.logger.info(f"Statistiques : {stats}")
        return stats

    async def train(self):

        # param_grid = {
        #     "swing_window": [21, 50, 75, 100, 150 , 200],
        #     "tp_pct": [1.0, 1.5, 2, 2.5, 3, 3.5],
        #     "sl_pct": [0.5, 1, 1.5, 2, 2.5]
        # }

        param_grid = {
            "swing_window": [21, 150 , 200],
            "tp_pct": [1.0, 1.5, 2, 2.5],
            "sl_pct": [0.5, 1.0, 1.5, 2]
        }

        trainer = BotTrainer(SweepBot, self.params)
        summary_df, results = await trainer.run(param_grid)

        return summary_df, results 


if __name__ == "__main__":

    # Lancer le bot en mode backtest
    # params = {
    #     "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
    #     "symbol": "ethusdc",
    #     "interval": "5m",
    #     "initial_capital": 1000,
    #     "swing_window": 100,
    #     "swing_side": 2,
    #     "tp_pct": 1.5,
    #     "sl_pct": 1.5
    # }

    # bot = SweepBot(params, "backtest")
    # summary_df, results = asyncio.run(bot.train())

    # pd.set_option('display.max_rows', None)
    # print(summary_df[[
    #     "name", "total_profit", "win_rate", "num_trades", "total_score",
    #     "swing_window", "tp_pct", "sl_pct"
    # ]])

    # stats = asyncio.run(bot.run())
    # print(stats)

    params = {
        "symbol": "ethusdc",
        "interval": "1m",
        "initial_capital": 1000,
        "swing_window": 21,
        "swing_side": 2,
        "tp_pct": 1.5,
        "sl_pct": 1.5
    }

    bot = SweepBot(params, "realtime")
    asyncio.run(bot.run())

    print("\n=== ✅ Bot terminé ===\n")