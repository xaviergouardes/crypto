# trading_bot/trader/trader.py
from datetime import datetime
from zoneinfo import ZoneInfo 

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose, StopBot

class TradeJournal:
    """Journalise tous les trades fermés et calcule le P&L total."""
    logger = Logger.get("TradeJournal")

    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._trades = []  # historique des trades fermés
        self._total_pnl = 0.0
        self._pnl_total_avec_frais = 0.0
        self._frais_par_transaction = 0.01

        self._event_bus.subscribe(TradeClose, self._on_trade_close)
        
    async def _on_trade_close(self, event: TradeClose):
        """
        Traite la fermeture d'un trade et calcule le PnL en tenant compte de la taille et des frais.
        event doit contenir :
        - side : "BUY" ou "SELL"
        - price : prix d'entrée
        - tp : take profit
        - sl : stop loss
        - size : taille de la position
        - target : "TP" ou "SL"
        - timestamp : date/heure du trade
        """

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

        # Enregistrer le trade dans le journal
        trade_record = {
            "side": event.side,
            "entry": event.price,
            "tp": event.tp,
            "sl": event.sl,
            "size": event.size,
            "target": event.target,
            "open_timestamp": event.open_timestamp,
            "close_timestamp": event.close_timestamp,
            "pnl": pnl
        }
        self._trades.append(trade_record)

        # Mettre à jour le PnL total et le PnL après frais
        self._total_pnl += pnl
        self._pnl_total_avec_frais = self._total_pnl - (self._frais_par_transaction * len(self._trades) * event.size)

        # Journaliser avec couleur selon PnL
        color = "🟢" if pnl >= 0 else "🔴"
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{color} Journal] Trade fermé - : {trade_record} | "
        #     f"P&L = {pnl:.2f} | Total = {self._total_pnl:.2f} | Total - Frais = {self._pnl_total_avec_frais:.2f}")

        paris_tz = ZoneInfo("Europe/Paris")

        # Conversion des timestamps en heure de Paris
        open_time_paris = trade_record["open_timestamp"].astimezone(paris_tz)
        close_time_paris = trade_record["close_timestamp"].astimezone(paris_tz)

        self.logger.debug(
            f"[{color}] "
            f"Trade {trade_record['side'].ljust(4)} [{open_time_paris.strftime('%Y-%m-%d %H:%M:%S')} / "
            f"{close_time_paris.strftime('%Y-%m-%d %H:%M:%S')}] : "
            f"Qty = {trade_record["size"]} | "
            f"P&L = {pnl:.2f} | Total = {self._total_pnl:.2f} | Total - Frais = {self._pnl_total_avec_frais:.2f}"
        )
        self.logger.debug(f"Summary {self.summary()} ")
                        
    def get_trades_journal(self):
        trades =  self._trades.copy()
        return trades
    
    def summary(self):
        """Retourne un résumé global du journal avec win rate par type de trade."""
        total_trades = len(self._trades)
        wins = len([t for t in self._trades if t["pnl"] > 0])
        losses = total_trades - wins

        # Séparer BUY et SELL
        buy_trades = [t for t in self._trades if t["side"] == "BUY"]
        sell_trades = [t for t in self._trades if t["side"] == "SELL"]

        wins_buy = len([t for t in buy_trades if t["pnl"] > 0])
        wins_sell = len([t for t in sell_trades if t["pnl"] > 0])

        win_rate_buy = (wins_buy / len(buy_trades) * 100) if buy_trades else 0
        win_rate_sell = (wins_sell / len(sell_trades) * 100) if sell_trades else 0

        # Calcul du PnL cumulé
        cumulative_pnls = []
        running_total = 0
        for t in self._trades:
            running_total += t["pnl"]
            cumulative_pnls.append(running_total)

        pnl_min = min(cumulative_pnls) if cumulative_pnls else 0
        pnl_max = max(cumulative_pnls) if cumulative_pnls else 0

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "total_pnl": self._total_pnl,
            "pnl_min": pnl_min,
            "pnl_max": pnl_max,
            "win_rate": (wins / total_trades) * 100 if total_trades > 0 else 0,
            "win_rate_buy": win_rate_buy,
            "win_rate_sell": win_rate_sell
        }


