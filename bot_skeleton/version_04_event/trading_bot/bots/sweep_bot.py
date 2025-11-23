
import asyncio
import logging

from trading_bot.core.logger import Logger

from trading_bot.core.event_bus import EventBus

from trading_bot.engine.realtime_engine import RealTimeEngine
from trading_bot.engine.backtest_engine import BacktestEngine

from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

from trading_bot.trainer.trainer import BotTrainer


class SweepBot:

    logger = Logger.get("SweepBot")

    # def __init__(self, params, mode):
    def __init__(self, params):

        self.event_bus = EventBus()
        self.system_trading = SimpleSweepSystemTrading(self.event_bus, params)   
        self.params = params

        self.logger.info(f"Bot {self.__class__.__name__} Initilisation Terminée.")

    async def run(self):
        self.engine = RealTimeEngine(self.event_bus, self.system_trading, self.params)
        await self.engine.run()
        # pas de code après car boucle infinie

    
    async def backtest(self, params:dict):
        self.engine = BacktestEngine(self.event_bus, self.system_trading, params)
        stats = await self.engine.run()
        # self.logger.info(f"Statistiques : {stats}")
        return stats