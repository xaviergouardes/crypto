# trading_bot/core/real_time_bot.py
import pandas as pd
import asyncio

from trading_bot.data_market.candle_source_csv import CandleSourceCsv
from trading_bot.data_market.candle_source_binance import CandleSourceBinance
from trading_bot.data_market.candle_source import CandleSource

from trading_bot.indicator.max import Max
from trading_bot.indicator.ema import Ema
from trading_bot.indicator.swing_detector import SwingDetector
from trading_bot.indicator.sweep_detector import SweepDetector

from trading_bot.strategie.sweep import SweepStrategy
from trading_bot.strategie.alternating import RandomAlternatingStrategy

from trading_bot.filter.wick_filter import WickFilter

from trading_bot.risk_manager.risk_manager import RiskManager
from trading_bot.trader.trader_only_one_position import OnlyOnePositionTrader

from trading_bot.journal.portefolio import Portfolio
from trading_bot.journal.statistiques import Statistiques

from trading_bot.journal.telegram_notifier import TelegramNotifier

class RealTimeBot:
    def __init__(self, params: dict = None, mode="realtime"):
        """
        mode: 'realtime' ou 'backtest'
        """

        self.mode = mode  # "realtime" ou "backtest"
        default_params = {
            "realtime": {
                "symbol": "ethusdc",
                "interval": "5m",
                "warmup_count": None,
            },
            "backtest": {
                "path": None,
            },
            "initial_capital": 1000,
            "ema_fast": 7,
            "ema_slow": 21,
            "swing_window": 200,
            "swing_side": 2,
            "tp_pct": 2.5,
            "sl_pct": 1
        }
        self.params = {**default_params, **(params or {})}

        if self.mode == "realtime" :               
            # Warmup = max de tous les paramètres numériques (sauf initial_capital)
            excluded = {"initial_capital", "swing_side", "tp_pct", "sl_pct"}  # si tu veux en exclure d’autres
            numeric_values = [v for k, v in self.params.items() if k not in excluded and isinstance(v,(int,float))]
            print("==>", max(numeric_values))
            self.params["realtime"]["warmup_count"] = max(numeric_values)
            self.params.pop("backtest", None)

            self.candle_source = CandleSourceBinance(symbol=self.params["realtime"]["symbol"], 
                                                     interval=self.params["realtime"]["interval"], 
                                                     warmup_count=self.params["realtime"]["warmup_count"])

        else:
            self.params.pop("realtime", None)

            self.candle_source = CandleSourceCsv(self.params["backtest"]["path"])

        self.df = None
        self.statistiques = None

        print(f"✅ Bot en mode {self.mode} initilisation ....")
        print(f"{self.params}")
         

        self._initialize_bot()

    def _initialize_bot(self):
        
        p = self.params

        if self.mode == "backtest":
            # On charge tout le CSV pour le backtest
            df = self.candle_source.get_initial_data().copy()
            df, stats = self._run_pipeline(df, warmup=True)
            self.df = df
            self.statistiques = stats
            print(f"✅ Backtest terminé sur {len(df)} bougies")
            if hasattr(stats, "summary"):
                print(stats.summary())
            else:
                print(stats)

        elif self.mode == "realtime":
            # On charge seulement le warmup pour initialiser les indicateurs
            df = self.candle_source.get_initial_data().head(p["realtime"]["warmup_count"]).copy()
            df, _ = self._run_pipeline(df, warmup=True)
            self.df = df
            print(f"✅ Bot temps réel initialisé avec {len(df)} bougies de warmup")


    async def start(self):
        if self.mode == "backtest":
            print("Mode backtest : pas de flux temps réel")
            return

        # Stream en temps réel à partir de la bougie suivante au warmup
        await self.candle_source.stream_candles(self.on_new_candle)

    async def on_new_candle(self, candle):
        # Ajouter la nouvelle bougie au DataFrame
        self.df = pd.concat([self.df, pd.DataFrame([candle])], ignore_index=True)

        # Recalculer pipeline uniquement sur toute la DF
        self.df, _ = self._run_pipeline(self.df)

        # last_row = self.df.iloc[-1]
        # if last_row['position'] in ["CLOSE_BUY_TP", "CLOSE_SELL_TP", "CLOSE_BUY_SL", "CLOSE_SELL_SL"]:
        #     print(last_row[['timestamp_paris', 'close', 'signal', 'entry_price', 'tp', 'sl', 'position', 'capital', 'trade_pnl', 'trade.id']])

        # Affichage uniquement de la dernière bougie
        # latest = self.df.iloc[-1]
        # print(f"{latest['timestamp']} |   "
        #       f"timestamp_paris={latest['timestamp_paris']} | "
        #       f"close={latest['close']} | "
        #       f"swing_high={latest['swing_high']} | "
        #       f"swing_low={latest['swing_low']}   "
        #       )
        

    def _run_pipeline(self, df, warmup=False):
        p = self.params

        df = df.copy()

        # Exemple simple avec tous les indicateurs et stratégie

        df = Ema(df).add_ema(p["ema_fast"])
        df = Ema(df).add_ema(p["ema_slow"])
        df = SwingDetector(df, window=p["swing_window"], side=p["swing_side"]).detect()
        df = SweepDetector(df).detect()

        df = SweepStrategy(df).generate_signals()
        # df = RandomAlternatingStrategy(df).generate_signals(p["realtime"]["warmup_count"])

        # wick_filter = WickFilter(df)
        # df = wick_filter.apply_filter()

        df = RiskManager(df, tp_pct=p["tp_pct"], sl_pct=p["tp_pct"]).calculate_risk()
        df = OnlyOnePositionTrader(df).run_trades()

        df = Portfolio(df, initial_capital=p["initial_capital"]).run_portfolio()

        # print(list(df.columns)) # affiche une vraie liste Python

        # # Crée les statistiques seulement si mode backtest
        stats = None
        if self.mode == "backtest":
            filtered_df = df[df['position'].isin(["CLOSE_BUY_TP", "CLOSE_SELL_TP", "CLOSE_BUY_SL", "CLOSE_SELL_SL"]) ]
            # print(filtered_df[['timestamp_paris', 'close', 'position',
            #                    'trade.begin', 'trade.end', 
            #                    'trade.entry_price', 'trade.id', 'trade.tp', 'trade.sl', 
            #                    'trade_pnl', 'capital']])
            stats = Statistiques(df, initial_capital=p["initial_capital"])

        # Affichage de la dernièr eligne calculé en fonction de la dernière bougie close uniquement hors warmup
        if not warmup:
            filtered_df = df[df['position'].isin(["CLOSE_BUY_TP", "CLOSE_SELL_TP", "CLOSE_BUY_SL", "CLOSE_SELL_SL"]) ]
            if not filtered_df.empty:
                last_row = filtered_df[['timestamp_paris', 'trade.id', 'position', 
                                'trade.begin', 'trade.end', 
                                'trade.entry_price', 'trade.tp', 'trade.sl', 
                                'trade_pnl', 'capital']].tail(1)
                csv_line = last_row.to_csv(index=False, header=False, sep=';')
                print(csv_line.strip())

                last_trade = last_row.iloc[0].to_dict()
                notifier = TelegramNotifier(token="8112934779:AAHwOejwOxsPd5bryocGXDbilwR7tH1hbiA", chat_id="6070936106")
                df = notifier.notify(last_trade)

        return df, stats


if __name__ == "__main__":
    # Exemple CSV

    # # Bot backtest
    # params = {
    #     "backtest": {
    #         "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv"
    #     },
    #     "initial_capital": 1000,
    #     "ema_fast": 7,
    #     "ema_slow": 21,
    #     "swing_window": 21,
    #     "swing_side": 2,
    #     "tp_pct": 1.6,
    #     "sl_pct": 1
    # }
    # bot = RealTimeBot(params=params, mode="backtest")

    # Bot temps réel
    params = {
        "realtime": {
            "symbol": "ethusdc",
            "interval": "1m"
        },
        "initial_capital": 1000,
        "ema_fast": 7,
        "ema_slow": 21,
        "swing_window": 21,
        "swing_side": 2,
        "tp_pct": 0.2,
        "sl_pct": 0.1
    }
    bot = RealTimeBot(params=params, mode="realtime")
    asyncio.run(bot.start())
