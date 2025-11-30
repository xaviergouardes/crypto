
import asyncio
import logging
from typing import override
import argparse

from trading_bot.bots.http.http_bot_server import HttpBotServer
from trading_bot.core.logger import Logger

from trading_bot.core.event_bus import EventBus
from trading_bot.core.startable import Startable

from trading_bot.bots.engine.realtime_engine import RealTimeEngine
from trading_bot.bots.engine.backtest_engine import BacktestEngine

from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

class SweepBot(Startable):

    logger = Logger.get("SweepBot")

    # def __init__(self, params, mode):
    def __init__(self, bot_id="sweep_bot_01"):
        super().__init__()

        self._event_bus = EventBus()

        self.bot_id = bot_id
        self.bot_type = "sweep_bot"
        
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
        self.logger.info(f"Mode backtest positioné")


    def set_realtime_mode(self):
        if self.is_running():
            raise Exception("Pas possible de changer le mode en cours d'execution !")
        self._mode = "realtime"
        self._engine = RealTimeEngine(self._event_bus, self._system_trading, self._params)
        self.logger.info(f"Mode realtime positioné")

    def sync(self, params: dict):
        if self.is_running():
            raise Exception("Impossible de changer les paramètres en cours d'exécution !")

        # -------------------------
        # 0. Helpers
        # -------------------------
        def deep_merge_trading_system(default_ts, incoming_ts):
            """Fusionne proprement les sous-clés trading_system sans écraser les defaults."""
            merged = default_ts.copy()
            for k, v in incoming_ts.items():
                merged[k] = v
            return merged

        # -------------------------
        # 1. Filtrer les paramètres inconnus
        # -------------------------
        default_keys = set(self._params.keys())
        incoming_keys = set(params.keys())

        # Paramètres inconnus = non présents dans les defaults
        unknown_keys = incoming_keys - default_keys
        if unknown_keys:
            unknown_params = {k: params[k] for k in unknown_keys}
            self.logger.warning(f"Paramètres inconnus ignorés : {unknown_params}")

        # On ne garde que les paramètres valides
        valid_params = {k: v for k, v in params.items() if k in default_keys}

        # -------------------------
        # 2. Merge profond et propre
        # -------------------------
        merged = self._params.copy()

        for key, value in valid_params.items():
            if key == "trading_system":
                merged["trading_system"] = deep_merge_trading_system(
                    self._params["trading_system"],
                    value
                )
            else:
                merged[key] = value

        # -------------------------
        # 3. Recalcule warmup
        # -------------------------
        self._params = self._compute_warmup_count(merged.copy())

        # -------------------------
        # 4. Re-crée les sous-systèmes
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
        return trades 

    @override
    async def _on_start(self) -> list:
        self.logger.info("SweepBot démarré.")
        trades_list = await self._engine.run()
        return trades_list

    @override
    def _on_stop(self):
        self._engine.stop()
        self._system_trading.stop()
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
    


# ----------------------------------------
# Lancement direct
# ----------------------------------------
if __name__ == "__main__":
    Logger.set_default_level(logging.INFO)

    # Logger.set_level("BotManagerServer", logging.DEBUG)
    # Logger.set_level("CommandDispatcher", logging.DEBUG)
    # Logger.set_level("BotManager", logging.DEBUG)
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("Backtest", logging.DEBUG)
        
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot_id", default="sweep_bot_01")
    parser.add_argument("--port", type=int, default=9101)
    args = parser.parse_args()

    # Création du bot avec paramètres dynamiques
    bot = SweepBot(bot_id=args.bot_id)
    http_server = HttpBotServer(bot, port=args.port)

    async def main():
        await http_server.start()
        await http_server.register()
        await http_server.wait_closed()

    asyncio.run(main())