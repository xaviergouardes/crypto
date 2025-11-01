# trading_bot/trader/trader.py
from datetime import datetime
from zoneinfo import ZoneInfo 

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose, StopBot, NewSoldes

class PortefolioManager:
    """Journalise tous les trades fermés et calcule le P&L total."""

    def __init__(self, event_bus: EventBus, starting_usdc: float = 1000):
        self.event_bus = event_bus
        
        # Soldes spot
        self.usdc_balance = starting_usdc

        # Subscribe to closing trades
        self.event_bus.subscribe(TradeClose, self.on_trade_close)
        self.event_bus.subscribe(StopBot, self.on_stop_bot)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [PortfolioManager] Initialisé | USDC={self.usdc_balance} ")

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

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Portfolio] Nouveau solde: {self.usdc_balance:.2f} USDC")
        await self.event_bus.publish(NewSoldes(
            usdc=self.usdc_balance,
            eth=0
        ))


    async def on_stop_bot(self, event: StopBot):
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [PortfolioManager] Soldes Finaux | USDC={self.usdc_balance} ")

    async def run(self):
        # Rien de spécial ici, l'écoute se fait via les événements
        pass
