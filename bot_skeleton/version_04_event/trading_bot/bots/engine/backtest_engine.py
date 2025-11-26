import pandas as pd

from trading_bot.core.event_bus import EventBus
from trading_bot.core.logger import Logger

from trading_bot.market_data.candle_source_csv import CandleSourceCsv
from trading_bot.bots.engine.engine import Engine
from trading_bot.system_trading.system import System

class BacktestEngine(Engine):

    logger = Logger.get("BacktestEngine")
      
    def __init__(self, event_bus:EventBus, system: System, params: dict):
        self._event_bus =  event_bus
        self._params = params
        self._system = system

        self._running = None

        self._candle_source = CandleSourceCsv(self._event_bus, self._params) 


    async def run(self) -> list:
        pass
        self._running = True
        
        # Démarrer le pipeline pour que les composants puissent capturer les events
        self._system.start_piepline()

        # Lancer la récupéreration des bougie de warnup
        await self._candle_source.warmup()

        # Boucle événementielle -> non bloqunte en backtest
        await self._candle_source.stream() 

        self.logger.debug(f" self._system.trader_journal : {self._system.get_trades_journal()} ")
        return self._system.get_trades_journal()


    def stop(self):
        self._running = False
        # Ajouter code pour arrêter proprement le candle_source si nécessaire


