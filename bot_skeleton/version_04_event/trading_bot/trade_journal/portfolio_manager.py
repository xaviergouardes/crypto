from datetime import datetime
from zoneinfo import ZoneInfo 

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose, StopBot, NewSoldes

class PortfolioManager:
    """Journalise tous les trades fermés et calcule le P&L total, ainsi que le solde max et min."""
    logger = Logger.get("PortfolioManager")

    def __init__(self, event_bus: EventBus, starting_usdc: float = 1000):
        self.event_bus = event_bus
        
        # Soldes spot
        self.usdc_balance = starting_usdc
        self.max_balance = starting_usdc
        self.min_balance = starting_usdc

        # Souscriptions
        self.event_bus.subscribe(TradeClose, self.on_trade_close)
        self.event_bus.subscribe(StopBot, self.on_stop_bot)

        self.logger.info(f"Initialisé | USDC={self.usdc_balance:.2f} "
              f"(max={self.max_balance:.2f}, min={self.min_balance:.2f})")

    async def on_trade_close(self, event: TradeClose) -> None:

        # Déterminer le prix de clôture en fonction du target
        if event.target == "TP":
            close_price = event.tp
        elif event.target == "SL":
            close_price = event.sl
        else:
            close_price = event.price.price  # fallback

        # Calcul du PnL en tenant compte du type de trade et de la taille
        pnl = 0.0
        if event.side == "BUY":
            pnl = (close_price - event.price.price) * event.size
        elif event.side == "SELL":
            pnl = (event.price.price - close_price) * event.size

        # Mise à jour du solde
        self.usdc_balance += pnl

        # Mise à jour solde max/min
        if self.usdc_balance > self.max_balance:
            self.max_balance = self.usdc_balance
        if self.usdc_balance < self.min_balance:
            self.min_balance = self.usdc_balance

        # Log clair
        self.logger.info(f"Solde={self.usdc_balance:.2f} | "
              f"Max={self.max_balance:.2f} | Min={self.min_balance:.2f}")

        # Publication de l'état du portefeuille
        await self.event_bus.publish(NewSoldes(
            usdc=self.usdc_balance,
            eth=0
        ))

    async def on_stop_bot(self, event: StopBot):
        self.logger.info(f"Soldes finaux | USDC={self.usdc_balance:.2f} | "
              f"Max={self.max_balance:.2f} | Min={self.min_balance:.2f}")

