import asyncio
from typing import override
import pandas as pd

from trading_bot.core.event_bus import EventBus

from trading_bot.core.logger import Logger
from trading_bot.core.startable import Startable
from trading_bot.market_data.candle_source_binance import CandleSourceBinance

from trading_bot.trade_journal.telegram_notifier import TelegramNotifier

class RealTimeEngine(Startable):
      
    _logger = Logger.get("RealTimeEngine")

    def __init__(self, event_bus:EventBus, params: dict):
        super().__init__() 
        self._event_bus =  event_bus
        self._params = params

        self._candle_source = CandleSourceBinance(self._event_bus, self._params) 
        self._telegram_notifier = TelegramNotifier(self._event_bus, self._params) 

    @override
    async def _on_start(self):
        self._logger.info("Démarrage demandé")

        # Lancement du flux de candle via le websocket
        await self._candle_source.start()


    @override
    def _on_stop(self):
        self._logger.info("Arret demandé")
        self._candle_source.stop()
        # Ajouter code pour arrêter proprement le candle_source si nécessaire

