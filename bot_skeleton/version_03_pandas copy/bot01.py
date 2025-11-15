
import argparse
import yaml
import sys

# from trading_bot.systems.sweep_system import SweepSystem
from trading_bot.systems.alea_system import AleaSystem

from trading_bot.engine.backtest_engine import BacktestEngine
from trading_bot.engine.realtime_engine import RealTimeEngine

class TradingBot:
    def __init__(self, params, mode):
        self.params = params
        # self.system = SweepSystem(params)
        self.system = AleaSystem(params)

        if mode == "backtest":
            self.engine = BacktestEngine(self.system, path=params["backtest"]["path"])
        else:
            self.engine = RealTimeEngine(self.system, self.params)

    def run(self):
        self.engine.run()


if __name__ == "__main__":

    # Lancer le bot en mode backtest
    # params = {
    #     "backtest": {
    #         "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv"
    #     },
    #     "initial_capital": 1000,
    #     "ema_fast": 7,
    #     "ema_slow": 21,
    #     "swing_window": 21,
    #     "swing_side": 2,
    #     "tp_pct": 1.6,
    #     "sl_pct": 1
    # }

    # bot = TradingBot(params, "backtest")
    # bot.run()

    params = {
        "symbol": "ethusdc",
        "interval": "1m",
        "warmup_count": 3,
        "initial_capital": 1000,
        "tp_pct": 0.1,
        "sl_pct": 0.05
    }

    bot = TradingBot(params, "realtime")
    bot.run()

    print("\n=== ✅ Bot terminé ===\n")