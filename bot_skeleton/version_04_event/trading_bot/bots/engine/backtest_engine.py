from typing import override
import pandas as pd

from trading_bot.core.event_bus import EventBus
from trading_bot.core.logger import Logger

from trading_bot.core.startable import Startable
from trading_bot.market_data.candle_source_csv import CandleSourceCsv
from trading_bot.system_trading.system import System

class BacktestEngine(Startable):

    logger = Logger.get("BacktestEngine")
      
    def __init__(self, event_bus:EventBus, system: System, params: dict):
        super().__init__() 
        self._event_bus =  event_bus
        self._params = params
        self._system = system

        self._candle_source = CandleSourceCsv(self._event_bus, self._params) 

    @override
    async def _on_start(self):
        """Démarre le pipeline de traitement"""
        self.logger.info("Démarrage demandé")

         # Démarrer la lecture du fichier csv
        await self._candle_source.start()

        # Attendre la fin de la lecture du fichier csv
        await self._candle_source.join()

        self.logger.debug(f" self._system.trader_journal : {self._system.get_trades_journal()} ")
        return self._system.get_trades_journal()

    @override
    def _on_stop(self):
         self.logger.info("Arret demandé")
         self._candle_source.stop()


