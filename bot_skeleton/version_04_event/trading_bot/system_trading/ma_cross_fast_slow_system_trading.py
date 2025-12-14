# trading_bot/main.py
#
# trading_bot/main.py
#
# Test avec les bougies et historique sur 25 bougie d'une minutes
# Stratégie basée sur la pente de la SMA avec une période de 25 bougie de 1 minutes
#


from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus

from trading_bot.indicators.moving_average.moving_average import MovingAverage
from trading_bot.indicators.ema_cross_detector.ema_cross_detector import EmaCrossDetector

from trading_bot.signal_engines.ma_cross_fast_slow_signal_engine import MaCrossFastSlowSignalEngine

from trading_bot.risk_manager.risk_manager import RiskManager 

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition

from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.portfolio_manager import PortfolioManager


class MaCrossFastSlowSystemTrading():
    """
    Implémente le système de trading, la stratégie.
    N'a pas besoin d'etre startable car tous ces composants sont ré-instancier systématiquement au démarrage du bot
    afin de garantir la prise en compte des bon paramétrage t du bon warmup
    """

    _logger = Logger.get("MaCrossFastSlowSystemTrading")

    def __init__(self, event_bus: EventBus, params:dict):
        self.event_bus =  event_bus
        self.params = params

        self._logger.info(f"Demmarage demandé")

        p = self.params

        self._ema_fast = MovingAverage(
            event_bus, 
            period=p["trading_system"]["fast_period"], 
            mode="EMA"
        )

        self._ema_slow = MovingAverage(
            event_bus, 
            period=p["trading_system"]["slow_period"], 
            mode="EMA"
        )
     
        self._indicator_ema_cross_detector = EmaCrossDetector(
                self.event_bus,               
                fast_period=p["trading_system"]["fast_period"],  
                slow_period=p["trading_system"]["slow_period"], 
                min_gap=p["trading_system"]["min_gap"],  
                slope_threshold=p["trading_system"]["slope_threshold"]
            )

        self.signal_engine = MaCrossFastSlowSignalEngine(
                self.event_bus, 
                periode_fast_ema=p["trading_system"]["fast_period"], 
                periode_slow_ema=p["trading_system"]["slow_period"]
            )      
        
        self.risk_manager = RiskManager(self.event_bus, tp_percent=p["trading_system"]["tp_pct"], sl_percent=p["trading_system"]["sl_pct"], solde_disponible=p["initial_capital"])     
        self.trader = TraderOnlyOnePosition(self.event_bus)
        
        self.trader_journal = TradeJournal(self.event_bus)
        self.portefolio_manager = PortfolioManager(self.event_bus, starting_usdc=p["initial_capital"])

        self._logger.info(f"Demmarage Terminé")


    def get_trades_journal(self) -> list:
        trades =  self.trader_journal.get_trades_journal()
        return trades