# trading_bot/main.py
#
# trading_bot/main.py
#
# Test avec les bougies et historique sur 25 bougie d'une minutes
# Stratégie basée sur la pente de la SMA avec une période de 25 bougie de 1 minutes
#


from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus

from trading_bot.indicators.indicator_rsi.indicator_rsi import IndicatorRSI
from trading_bot.signal_engines.rsi_cross_signal_engine import RSICrossSignalEngine

from trading_bot.indicators.atr_filter.indicator_atr import IndicatorAtr

from trading_bot.risk_manager.risk_manager import RiskManager 

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition

from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.portfolio_manager import PortfolioManager


class RSICrossSystemTrading():
    """
    Implémente le système de trading, la stratégie.
    N'a pas besoin d'etre startable car tous ces composants sont ré-instancier systématiquement au démarrage du bot
    afin de garantir la prise en compte des bon paramétrage t du bon warmup
    """

    _logger = Logger.get("RSICrossSystemTrading")

    def __init__(self, event_bus: EventBus, params:dict):
        self.event_bus =  event_bus
        self.params = params

        self._logger.info(f"Demmarage demandé")

        p = self.params

        self.ema_fast = IndicatorRSI(
            event_bus, 
            period=p["trading_system"]["rsi_fast_period"]
        )

        self.ema_slow = IndicatorRSI(
            event_bus, 
            period=p["trading_system"]["rsi_slow_period"]
        )
     
        self.atr = IndicatorAtr(
            event_bus, 
            period=p["trading_system"]["atr_period"]
        )  

        self.signal_engine = RSICrossSignalEngine(
                self.event_bus, 
                rsi_fast_period=p["trading_system"]["rsi_fast_period"], 
                rsi_slow_period=p["trading_system"]["rsi_slow_period"]
            )   

        
        self.risk_manager = RiskManager(
            self.event_bus, 
            tp_percent=p["trading_system"]["tp_pct"], 
            sl_percent=p["trading_system"]["sl_pct"], 
            solde_disponible=p["initial_capital"],
            with_filter=p.get("trading_system", {}).get("filter", False)
            )     
        
        self.trader = TraderOnlyOnePosition(self.event_bus)
        
        self.trader_journal = TradeJournal(self.event_bus)
        self.portefolio_manager = PortfolioManager(self.event_bus, starting_usdc=p["initial_capital"])

        self._logger.info(f"Demmarage Terminé")


    def get_trades_journal(self) -> list:
        trades =  self.trader_journal.get_trades_journal()
        return trades