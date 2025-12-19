from trading_bot.signal_engines.price_cross_ema_signal_engine import PriceCrossEmaSignalEngine
from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus

from trading_bot.indicators.moving_average.moving_average import MovingAverage

from trading_bot.risk_manager.risk_manager import RiskManager 

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition

from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.portfolio_manager import PortfolioManager


class PriceCrossSystemTrading():
    """
    Implémente le système de trading, la stratégie.
    N'a pas besoin d'etre startable car tous ces composants sont ré-instancier systématiquement au démarrage du bot
    afin de garantir la prise en compte des bon paramétrage t du bon warmup
    """

    _logger = Logger.get("PriceCrossSystemTrading")

    def __init__(self, event_bus: EventBus, params:dict):
        self.event_bus =  event_bus
        self.params = params

        self._logger.info(f"Demmarage demandé")

        p = self.params

        self._ema = MovingAverage(
            event_bus, 
            period=p["trading_system"]["ema_period"], 
            mode="EMA"
        )

        self.signal_engine = PriceCrossEmaSignalEngine(
                self.event_bus, 
                ema_period=p["trading_system"]["ema_period"]
            )      
        
        self.risk_manager = RiskManager(self.event_bus, tp_percent=p["trading_system"]["tp_pct"], sl_percent=p["trading_system"]["sl_pct"], solde_disponible=p["initial_capital"])     
        self.trader = TraderOnlyOnePosition(self.event_bus)
        
        self.trader_journal = TradeJournal(self.event_bus)
        self.portefolio_manager = PortfolioManager(self.event_bus, starting_usdc=p["initial_capital"])

        self._logger.info(f"Demmarage Terminé")


    def get_trades_journal(self) -> list:
        trades =  self.trader_journal.get_trades_journal()
        return trades