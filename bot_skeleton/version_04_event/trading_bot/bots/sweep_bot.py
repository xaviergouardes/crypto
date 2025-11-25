
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


    def sync(self, params: dict):
        if self.is_running():
            raise Exception("Impossible de changer les paramètres en cours d'exécution !")

        # -------------------------
        # 1. Filtrer les paramètres inconnus
        # -------------------------
        default_keys = set(self._params.keys())
        incoming_keys = set(params.keys())

        # Paramètres inconnus = non présents dans les defaults
        unknown_keys = incoming_keys - default_keys
        if unknown_keys:
            # Construire un dict avec clé et valeur pour le log
            unknown_params = {k: params[k] for k in unknown_keys}
            self.logger.warning(f"Paramètres inconnus ignorés : {unknown_params}")

        # On ne garde que les paramètres valides
        valid_params = {k: v for k, v in params.items() if k in default_keys}

        # -------------------------
        # 2. Merge propre (les valid_params écrasent self._params)
        # -------------------------
        merged = {**self._params, **valid_params}

        # -------------------------
        # 3. Recalcule warmup
        # -------------------------
        self._params = self._compute_warmup_count(merged.copy())

        # -------------------------
        # 4. Recrée les sous-systèmes
        # -------------------------
        self._system_trading = SimpleSweepSystemTrading(self._event_bus, self._params)

        if self._mode == "realtime":
            self.set_realtime_mode()
        elif self._mode == "backtest":
            self.set_backtest_mode()

        # -------------------------
        # 5. Log final
        # -------------------------
        self.logger.info(f"Paramètres synchronisés : {self._params}")

    def get_trades_journal(self):
        trades = self._system_trading.get_trades_journal()    

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