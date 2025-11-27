# trading_bot/main.py
#
# trading_bot/main.py
#
# Test avec les bougies et historique sur 25 bougie d'une minutes
# Stratégie basée sur la pente de la SMA avec une période de 25 bougie de 1 minutes
#


from typing import override

from trading_bot.system_trading.system import System

from trading_bot.core.event_bus import EventBus

from trading_bot.indicators.indicator_simple_swing_detector import IndicatorSimpleSwingDetector
from trading_bot.signal_engines.simple_sweep_swing_signal_engine import  SimpleSweepSwingSignalEngine

from trading_bot.risk_manager.risk_manager import RiskManager 

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition

from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.portfolio_manager import PortfolioManager


class SimpleSweepSystemTrading(System):

    def __init__(self, event_bus: EventBus, params:dict):
        self.event_bus =  event_bus
        self.params = params

    @override
    def start_piepline(self):
        p = self.params
    
        self.indicator_swing_detector = IndicatorSimpleSwingDetector(self.event_bus, swing_side=p["trading_system"]["swing_side"], swing_window=p["trading_system"]["swing_window"])

        self.signal_engine = SimpleSweepSwingSignalEngine(self.event_bus)      
        
        self.risk_manager = RiskManager(self.event_bus, tp_percent=p["trading_system"]["tp_pct"], sl_percent=p["trading_system"]["sl_pct"], solde_disponible=p["initial_capital"])     
        self.trader = TraderOnlyOnePosition(self.event_bus)
        
        self.trader_journal = TradeJournal(self.event_bus)
        self.portefolio_manager = PortfolioManager(self.event_bus, starting_usdc=p["initial_capital"])

    def get_trades_journal(self) -> list:
        trades =  self.trader_journal.get_trades_journal()
        return trades