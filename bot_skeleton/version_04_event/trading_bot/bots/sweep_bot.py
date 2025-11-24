
import asyncio
import logging
from typing import override

from trading_bot.core.logger import Logger

from trading_bot.core.event_bus import EventBus
from trading_bot.core.startable import Startable

from trading_bot.bots.engine.realtime_engine import RealTimeEngine
from trading_bot.bots.engine.backtest_engine import BacktestEngine

from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

from trading_bot.trainer.trainer import BotTrainer


class SweepBot(Startable):

    logger = Logger.get("SweepBot")

    # def __init__(self, params, mode):
    def __init__(self):
        super().__init__()

        self._event_bus = EventBus()
        self._engine = None
        self._mode = None

        self._params = self._default_params()
        self._params = self._compute_warmup_count(self._params)

        self._system_trading = SimpleSweepSystemTrading(self._event_bus, self._params)  
        self.set_realtime_mode()

        self.logger.info(f"Bot {self.__class__.__name__} Initilisation Terminée.")

    # async def run(self):
    #     self.engine = RealTimeEngine(self._event_bus, self._system_trading, self.__params)
    #     await self.engine.run()
    #     # pas de code après car boucle infinie

    def set_backtest_mode(self):
        if self.is_running():
            raise Exception("Pas possible de changer le mode en cours d'execution !")
        self._mode = "backtest"
        self._engine = BacktestEngine(self._event_bus, self._system_trading, self._params)

    def set_realtime_mode(self):
        if self.is_running():
            raise Exception("Pas possible de changer le mode en cours d'execution !")
        self._mode = "realtime"
        self._engine = RealTimeEngine(self._event_bus, self._system_trading, self._params)

    def sync(self, params:dict):
        if self.is_running():
            raise Exception("Pas possible de changer les paramétres en cours d'execution !")
        self._params  = self._compute_warmup_count(params.copy())

        # Recrée le system de trading por prise en compte des nouveaux paramétres 
        self._system_trading = SimpleSweepSystemTrading(self._event_bus, self._params) 

        # Recrée l'engine pour refléter les nouveaux params
        if self._mode == "realtime":
            self.set_realtime_mode()
        elif self._mode == "backtest":
            self.set_backtest_mode()

        self.logger.info(f"Paramètres synchronisés : {self._params}")

    @override
    async def on_start(self):
        self.logger.info("SweepBot démarré.")
        stats = await self._engine.run()
        return stats

    @override
    def on_stop(self):
        self._engine.stop()
        self._system_trading.stop()
        self.logger.info("SweepBot arrêté.")

    def _default_params(self) -> dict:
        return {
            "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
            "symbol": "ethusdc",
            "interval": "5m",
            "initial_capital": 1000,
            "swing_window": 200,
            "swing_side": 2,
            "tp_pct": 2.5,
            "sl_pct": 0.5
        }

    def _compute_warmup_count(self, params:dict) -> dict:
        return_params = params.copy()
        warmup_count = return_params["swing_window"]
        return_params["warmup_count"] = warmup_count
        return return_params