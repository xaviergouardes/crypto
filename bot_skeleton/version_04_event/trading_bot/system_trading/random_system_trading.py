# trading_bot/main.py
#
# trading_bot/main.py
#
# Test avec les bougies et historique sur 25 bougie d'une minutes
# Stratégie basée sur la pente de la SMA avec une période de 25 bougie de 1 minutes
#

import asyncio
from datetime import datetime, timedelta

from trading_bot.core.event_bus import EventBus

from trading_bot.indicators.indicator_simple_swing_detector import IndicatorSimpleSwingDetector

from trading_bot.signal_engines.random_signal_engine import RandomSignalEngine

from trading_bot.risk_manager.risk_manager import RiskManager 

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition

from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.telegram_notifier import TelegramNotifier
from trading_bot.trade_journal.portfolio_manager import PortfolioManager


class RandomSystemTrading:

    def __init__(self, event_bus, params:dict):
        self.event_bus =  event_bus
        self.params = params
        p = self.params

        signal_engine = RandomSignalEngine(self.event_bus)      
        
        risk_manager = RiskManager(self.event_bus, tp_percent=p["tp_pct"], sl_percent=p["sl_pct"], solde_disponible=p["initial_capital"])     
        trader = TraderOnlyOnePosition(self.event_bus)
        
        trader_journal = TradeJournal(self.event_bus)
        portefolio_manager = PortfolioManager(self.event_bus, starting_usdc=p["initial_capital"])
