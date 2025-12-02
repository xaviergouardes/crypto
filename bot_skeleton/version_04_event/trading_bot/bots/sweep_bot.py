
import asyncio
import logging
from typing import override
import argparse

from trading_bot.core.logger import Logger

from trading_bot.core.event_bus import EventBus
from trading_bot.core.startable import Startable

from trading_bot.bots.engine.realtime_engine import RealTimeEngine
from trading_bot.bots.engine.backtest_engine import BacktestEngine

from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

class SweepBot(Startable):

    logger = Logger.get("SweepBot")

    # def __init__(self, params, mode):
    def __init__(self, bot_id="sweep_bot_01", params:dict = None):
        super().__init__()

        self._event_bus = EventBus()

        self.bot_id = bot_id
        self.bot_type = "sweep_bot"
        
        self._mode = None
        self._engine = None
        self._system_trading = None

        if params is None : 
            self._params = self._default_params()
        else:
            self._params = params
        self._params = self._compute_warmup_count(self._params)

        self.logger.info(f"Bot {self.__class__.__name__} Initilisation Terminée.")


    def set_backtest_mode(self):
        if self.is_running():
            raise Exception("Pas possible de changer le mode en cours d'execution !")
        self._mode = "backtest"
        self.logger.info(f"Mode backtest positioné")


    def set_realtime_mode(self):
        if self.is_running():
            raise Exception("Pas possible de changer le mode en cours d'execution !")
        self._mode = "realtime"
        self.logger.info(f"Mode realtime positioné")


    def sync(self, params: dict):
        if self.is_running():
            raise Exception("Impossible de changer les paramètres en cours d'exécution !")

        def merge_dicts(default: dict, update: dict) -> dict:
            """Merge profond limité au 1er niveau pour les sous-dicts."""
            result = default.copy()
            for k, v in update.items():
                if isinstance(v, dict) and isinstance(result.get(k), dict):
                    result[k] = {**result[k], **v}
                else:
                    result[k] = v
            return result

        # --- 1. Filtrer les paramètres inconnus ---
        default_keys = set(self._params.keys())
        valid_params = {k: v for k, v in params.items() if k in default_keys}

        unknown_keys = set(params) - default_keys
        if unknown_keys:
            self.logger.warning(f"Paramètres inconnus ignorés : "
                                f"{ {k: params[k] for k in unknown_keys} }")

        # --- 2. Merge propre et automatique ---
        merged = merge_dicts(self._params, valid_params)

        # --- 3. Warmup ---
        self._params = self._compute_warmup_count(merged)

        self.logger.info(f"Paramètres synchronisés : {self._params}")


    def get_trades_journal(self):
        trades = self._system_trading.get_trades_journal()   
        return trades 

    @override
    async def _on_start(self) -> list:
        self.logger.info("Demarrage Demandé.")

        self._system_trading = SimpleSweepSystemTrading(self._event_bus, self._params)

        if self._mode == "realtime":
            self._engine = RealTimeEngine(self._event_bus, self._params)
        elif self._mode == "backtest":
            self._engine = BacktestEngine(self._event_bus, self._params)
        else:
            raise ValueError(f"Mode inconnu : {self._mode}. Valeurs acceptées : realtime, backtest.")
        
        await self._engine.start()

        trades_list = self._system_trading.get_trades_journal()
        return trades_list

    @override
    def _on_stop(self):
        if self.is_running():
            self._engine.stop()
            # Pour libérer les objets qui sont abonée sur le bus
            self._event_bus.unsubscribe_all()
            # Pour etre sur que l'aobjet soit bien rétinstancier
            self._system_trading = None
            self.logger.info("SweepBot arrêté.")

    def _default_params(self) -> dict:
        return {
            "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
            "symbol": "ethusdc",
            "interval": "5m",
            "initial_capital": 1000,
            "trading_system": {
                "swing_window": 200,
                "swing_side": 2,
                "tp_pct": 2.5,
                "sl_pct": 0.5,
            }
        }

    def _compute_warmup_count(self, params:dict) -> dict:
        return_params = params.copy()
        warmup_count = return_params["trading_system"]["swing_window"]
        return_params["trading_system"]["warmup_count"] = warmup_count
        return return_params
    

