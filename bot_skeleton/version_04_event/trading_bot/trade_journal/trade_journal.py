# trading_bot/trader/trader.py
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd 

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose
from trading_bot.trainer.statistiques_engine import StatsEngine
from trading_bot.trainer.statistiques_engine import *

class TradeJournal:
    """Journalise tous les trades fermés et calcule le P&L total."""
    logger = Logger.get("TradeJournal")

    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._trades = []  # historique des trades fermés
        self._total_pnl = 0.0
        self._pnl_total_avec_frais = 0.0
        self._frais_par_transaction = 0.01

        self.stats_engine = StatsEngine(indicators=[
            TotalProfitIndicator(),
            WinRateIndicator(),
            NumTradesIndicator(),
            MaxDrawdownIndicator(),
            MaxWinningStreakIndicator(),
            NormalizedScoreIndicator(weights={
                "s_total_profit": 0.3,
                "s_win_rate": 0.4,
                "s_max_drawdown_pct": 0.2,
                "s_num_trades": 0.1
            })
        ])
        
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

        # Analyse via StatsEngine
        stats, trades_list = self.stats_engine.analyze(
            df=pd.DataFrame(self._trades),
        )
        self.logger.info(" | ".join(f"{k}: {float(v):.4f}" if isinstance(v, float) or hasattr(v, 'item') else f"{k}: {v}" for k, v in stats.items()))
                        
    def get_trades_journal(self) -> list:
        trades =  self._trades.copy()
        return trades
    

