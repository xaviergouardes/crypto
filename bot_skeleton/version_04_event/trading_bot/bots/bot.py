
from typing import override
import copy

from datetime import datetime, timedelta, timezone
from typing import Optional

from trading_bot.bots import BOTS_CONFIG
from trading_bot.core.event_bus import EventBus

from trading_bot.core.logger import Logger

from trading_bot.bots.engine.realtime_engine import RealTimeEngine
from trading_bot.bots.engine.backtest_engine import BacktestEngine
from trading_bot.core.startable import Startable

from trading_bot.trainer.statistiques_engine import *

class Bot(Startable):

    # def __init__(self, params, mode):
    def __init__(self, bot_type="bot_type", bot_id="bot_01", params:dict = None):
        super().__init__()

        self.logger = Logger.get(f"Bot {bot_type} {bot_id}")

        self.config = BOTS_CONFIG[bot_type]

        self._event_bus = EventBus()

        self.bot_id = bot_id
        self.bot_type = bot_type
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None

        self._mode = None
        self._engine = None
        self._system_trading = None

        if params is None : 
            self._params = copy.deepcopy(self.config["default_parameters"])
        else:
            self._params = params
        self._params = self._compute_warmup_count(self._params)

        self._params["bot_id"] = bot_id
        
        self.logger.info(f"Bot {self.bot_type} {self.bot_id} Initilisation Terminée.")

    @property
    def uptime(self) -> Optional[timedelta]:
        if self.started_at is None:
            return None
        return datetime.now(timezone.utc) - self.started_at

    @property
    def execution_time(self):
        if self.started_at and self.stopped_at:
            return self.stopped_at - self.started_at
        return None
    
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
        if self._system_trading is None:
            raise RuntimeError("System trading non initialisé")
        trades = self._system_trading.get_trades_journal()   
        return trades 

    def get_stats(self):    
        if self._system_trading is None:
            raise RuntimeError("System trading non initialisé")   
        trades = self._system_trading.get_trades_journal()   
        stats, trades_list = StatsEngine().analyze(
            df=pd.DataFrame(trades),
            params={**self._params}
        )
        return stats, trades_list
    
    @override
    async def _on_start(self) -> list:
        self.logger.info("Demarrage Demandé.")

        # on reinstalcie tout le System avec les paramétres en cours
        system_class = self.config["system_class"]
        self._system_trading = system_class(self._event_bus, self._params)

        if self._mode == "realtime":
            self._engine = RealTimeEngine(self._event_bus, self._params)
        elif self._mode == "backtest":
            self._engine = BacktestEngine(self._event_bus, self._params)
        else:
            raise ValueError(f"Mode inconnu : {self._mode}. Valeurs acceptées : realtime, backtest.")
        
        await self._engine.start()

        self.started_at = datetime.now(timezone.utc)

        # a quoi ça sert de renvoyer le journal des trades ?
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
            self.stopped_at = datetime.now(timezone.utc)
            self.logger.info(f"{self.bot_id} arrêté.")


    def _compute_warmup_count(self, params: dict) -> dict:
        """
        Met à jour le warmup_count en prenant le max des attributs listés dans warmup_rules.
        """
        return_params = params.copy()
        trading_system = return_params.get("trading_system", {})    

        # Calcul automatique à partir de warmup_rules
        warmup_rules = BOTS_CONFIG[self.bot_type].get("warmup_rules", {})
        candidates = [
            trading_system[k] * v for k, v in warmup_rules.items() if k in trading_system
        ]
        warmup_count = max(candidates) if candidates else 0

        trading_system["warmup_count"] = warmup_count
        return_params["trading_system"] = trading_system

        return return_params
