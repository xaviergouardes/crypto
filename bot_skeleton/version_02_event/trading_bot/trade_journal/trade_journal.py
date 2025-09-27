# trading_bot/trader/trader.py
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose

class TradeJournal:
    """Journalise tous les trades fermés et calcule le P&L total."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.trades = []  # historique des trades fermés
        self.total_pnl = 0.0
        self.event_bus.subscribe(TradeClose, self.on_trade_close)

    async def on_trade_close(self, event: TradeClose):
        # Calcul du P&L pour ce trade
        pnl = 0.0
        if event.side == "BUY":
            if event.target == "TP":
                pnl = (event.tp - event.price) * event.size
            elif event.target == "SL":
                pnl = (event.sl - event.price) * event.size

        elif event.side == "SELL":
            if event.target == "TP":
                pnl = (event.price - event.tp) * event.size
            elif event.target == "SL":
                pnl = (event.price - event.sl) * event.size

        # Enregistrer le trade dans le journal
        trade_record = {
            "side": event.side,
            "entry": event.price,
            "tp": event.tp,
            "sl": event.sl,
            "size": event.size,
            "target": event.target,
            "pnl": pnl
        }
        self.trades.append(trade_record)
        self.total_pnl += pnl

        print(f"[📘 Journal] Trade fermé: {trade_record} | P&L = {pnl:.2f} | Total = {self.total_pnl:.2f}")

    def summary(self):
        """Retourne un résumé global du journal."""
        total_trades = len(self.trades)
        wins = len([t for t in self.trades if t["pnl"] > 0])
        losses = total_trades - wins
        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "total_pnl": self.total_pnl
        }

    async def run(self):
        # Rien de spécial ici, l'écoute se fait via les événements
        pass
