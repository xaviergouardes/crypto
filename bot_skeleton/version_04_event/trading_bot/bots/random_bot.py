
import asyncio
from trading_bot.core.event_bus import EventBus

from trading_bot.core.logger import Logger

from trading_bot.engine.realtime_engine import RealTimeEngine
from trading_bot.engine.backtest_engine import BacktestEngine
from trading_bot.system_trading.random_system_trading import RandomSystemTrading

class RandomBot:
    logger = Logger.get("RandomBot")

    def __init__(self, params, mode):

        self.event_bus = EventBus()
        
        self.params = params
        self.system_trading = RandomSystemTrading(self.event_bus, params)   

        if mode == "backtest":
            self.engine = BacktestEngine(self.event_bus, self.system_trading, path=params["backtest"]["path"])
        else:
            self.engine = RealTimeEngine(self.event_bus, self.system_trading, self.params)

    def run(self):
        asyncio.run(self.engine.run())


if __name__ == "__main__":

    # Lancer le bot en mode backtest
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

    # bot = RandomBot(params, "backtest")
    # asyncio.run(bot.run())

    # params = {
    #     "symbol": "ethusdc",
    #     "interval": "1m",
    #     "warmup_count": 3,
    #     "initial_capital": 1000,
    #     "tp_pct": 0.1,
    #     "sl_pct": 0.05
    # }

    params = {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "1m",
        "warmup_count": 21,
        "initial_capital": 1000,
        "tp_pct": 0.05,
        "sl_pct": 0.025
    }

    bot = RandomBot(params, "realtime")
    bot.run()

    print("\n=== ✅ Bot terminé ===\n")