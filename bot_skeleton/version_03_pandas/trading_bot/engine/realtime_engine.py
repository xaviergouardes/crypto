

import asyncio
import pandas as pd

from trading_bot.data_market.candle_source_binance import CandleSourceBinance

from trading_bot.systems.system_abstract import System
from trading_bot.reporting.telegram_notifier import TelegramNotifier

from trading_bot.reporting.log_last_trade import LogLastTrade

class RealTimeEngine:

    def __init__(self, system: System, params: dict):
        self.system = system
        self.params = params

        symbol = params["symbol"]
        interval = params["interval"]

        # Priorité au warmup_count fourni dans les params
        warmup_count = params.get("warmup_count", None)

        if warmup_count is None:
            # Warmup = max de tous les paramètres numériques (sauf initial_capital)
            excluded = {"initial_capital", "swing_side", "tp_pct", "sl_pct"}  # si tu veux en exclure d’autres
            numeric_values = [v for k, v in self.params.items() if k not in excluded and isinstance(v,(int,float))]
            if numeric_values:
                warmup_count =  max(numeric_values)
            else:
                warmup_count =  0
            self.params["warmup_count"] = warmup_count

        # Récupéreation des bougies de warmup
        self.candle_source = CandleSourceBinance(symbol=symbol, interval=interval, warmup_count=warmup_count) 
        self.df = self.candle_source.get_initial_data().copy()

        # Initilisation des calculs dans le df 
        self.df, stats = self.system.run(self.df)

    def run(self):
        asyncio.run(self.candle_source.stream(self.on_new_candle))

    def on_new_candle(self, candle):

        # Ajouter la nouvelle Bougie au df
        self.df = pd.concat([self.df, pd.DataFrame([candle])], ignore_index=True)
        
        df = self.df.copy()
        df, stats = self.system.run(df)
        
        notifier = TelegramNotifier(token="8112934779:AAHwOejwOxsPd5bryocGXDbilwR7tH1hbiA", chat_id="6070936106")
        df = notifier.notify(df)

        df = LogLastTrade().log(df)


