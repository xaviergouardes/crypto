
import asyncio
from trading_bot.core.event_bus import EventBus

from trading_bot.core.logger import Logger
from trading_bot.market_data.candle_source_csv import CandleSourceCsv
from trading_bot.market_data.candle_source_binance import CandleSourceBinance

from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

class TradingBot:

    logger = Logger.get("TradingBot")

    def __init__(self, params, mode):

        self.event_bus = EventBus()
        
        self.params = params
        self.system_trading = SimpleSweepSystemTrading(self.event_bus, params)

        # Priorité au warmup_count fourni dans les params
        warmup_count = params.get("warmup_count", None)

        if warmup_count is None:
            # Warmup = max de tous les paramètres numériques (sauf initial_capital)
            excluded = {"initial_capital", "swing_side", "tp_pct", "sl_pct"}  # si tu veux en exclure d’autres
            numeric_values = [v for k, v in self.params.items() if k not in excluded and isinstance(v,(int,float))]
            if numeric_values:
                warmup_count =  max(numeric_values)
            else:
                warmup_count =  0
            self.params["warmup_count"] = warmup_count

        # Injection du bon CancdleSource
        if mode == "backtest":
            self.candle_source = CandleSourceCsv(self.event_bus, params)  

        else:
            self.candle_source = CandleSourceBinance(self.event_bus, params) 

    async def run(self):
        await self.candle_source.warmup()
        await self.candle_source.stream()
        print("Bot end !")


if __name__ == "__main__":

    # Lancer le bot en mode backtest
    params = {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "1m",
        "warmup_count": 21,
        "initial_capital": 1000,
        "ema_fast": 7,
        "ema_slow": 21,
        "swing_window": 21,
        "swing_side": 2,
        "tp_pct": 1.6,
        "sl_pct": 1
    }

    bot = TradingBot(params, "backtest")
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