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

from trading_bot.risk_manager.risk_manager import RiskManager
from trading_bot.trader.trader_only_one_position import OnlyOnePositionTrader

from trading_bot.journal.portefolio import Portfolio
from trading_bot.journal.statistiques import Statistiques
from trading_bot.journal.telegram_notifier_async import AsyncTelegramNotifier
from trading_bot.journal.telegram_notifier import TelegramNotifier

class RealTimeBot:
    def __init__(self, candle_source: CandleSource, warmup_count=0, mode="realtime", initial_capital=1000):
        """
        mode: 'realtime' ou 'backtest'
        """
        self.candle_source = candle_source
        self.warmup_count = warmup_count
        self.mode = mode  # "realtime" ou "backtest"
        self.initial_capital = initial_capital

        self.df = None
        self.statistiques = None

        self._initialize_bot()

    def _initialize_bot(self):
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
            df = self.candle_source.get_initial_data().head(self.warmup_count).copy()
            df, _ = self._run_pipeline(df, warmup=True)
            self.df = df
            print(f"✅ Bot temps réel initialisé avec {len(df)} bougies de warmup")
            # print(df.tail(2))
            print(df)

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
        #     print(last_row[['timestamp_paris', 'close', 'signal', 'entry_price', 'tp', 'sl', 'position', 'capital', 'trade_pnl', 'trade_id']])

        # Affichage uniquement de la dernière bougie
        # latest = self.df.iloc[-1]
        # print(f"{latest['timestamp']} |   "
        #       f"timestamp_paris={latest['timestamp_paris']} | "
        #       f"close={latest['close']} | "
        #       f"swing_high={latest['swing_high']} | "
        #       f"swing_low={latest['swing_low']}   "
        #       )
        

    def _run_pipeline(self, df, warmup=False):
        df = df.copy()

        # Exemple simple avec tous les indicateurs et stratégie

        df = Ema(df).add_ema(7)
        df = Ema(df).add_ema(21)
        df = SwingDetector(df, window=100, side=2).detect()
        df = SweepDetector(df).detect()

        df = SweepStrategy(df).generate_signals()
        # pd.set_option('display.max_rows', None)
        # Détecter uniquement les nouveaux swings par rapport à la ligne précédente
        df['new_swing_high'] = df['last_swing_high'].ne(df['last_swing_high'].shift(1))
        df['new_swing_low']  = df['last_swing_low'].ne(df['last_swing_low'].shift(1))

        # Filtrer les lignes où il y a un swing high ou low
        new_swings = df[df['new_swing_high'] | df['new_swing_low']]

        # Afficher les 10 premiers swings détectés
        print(new_swings[['timestamp_paris', 'last_swing_high', 'last_swing_low']])


        # df = RandomAlternatingStrategy(df).generate_signals()

        df = RiskManager(df, tp_pct=2, sl_pct=0.6).calculate_risk()
        df = OnlyOnePositionTrader(df).run_trades()

        df = Portfolio(df, initial_capital=self.initial_capital).run_portfolio()

        # notifier = TelegramNotifier(token="8112934779:AAHwOejwOxsPd5bryocGXDbilwR7tH1hbiA", chat_id="6070936106")
        # df = notifier.notify(df)

        # print(list(df.columns)) # affiche une vraie liste Python

        # # Crée les statistiques seulement si mode backtest
        stats = None
        if self.mode == "backtest":
            filtered_df = df[df['position'].isin(["CLOSE_BUY_TP", "CLOSE_SELL_TP", "CLOSE_BUY_SL", "CLOSE_SELL_SL"]) ]
            print(filtered_df[['timestamp_paris', 'close', 'signal', 'entry_price', 'tp', 'sl', 'position', 'capital', 'trade_pnl', 'trade_id']])
            stats = Statistiques(df, initial_capital=self.initial_capital)

        # Affichage signal uniquement hors warmup
        if not warmup:

            print(df[['timestamp_paris', 
                      'close', 'signal', 
                      'entry_price', 'tp', 'sl', 'tp_pct', 'sl_pct', 
                      'position', 
                      'trade_id', 'trade.tp', 'trade.sl', 'trade_pnl',
                      'capital']]
                      .tail(1).to_string(index=False, header=False)
                      )
            
            # print(df[['timestamp_paris', 
            #           'close', 'signal', 
            #           'entry_price', 'tp', 'sl', 'tp_pct', 'sl_pct', 
            #           'position', 
            #           'trade_id', 'trade.tp', 'trade.sl', 'trade_pnl',
            #           'capital']])
            # latest = df.iloc[-1]
            # if pd.notna(latest.get("signal")):
            #     print(f"🚀 Signal détecté à {latest['timestamp']} : {latest['signal']}")

        return df, stats


if __name__ == "__main__":
    # Exemple CSV

    # Bot backtest
    source = CandleSourceCsv(
        "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250901_20251104.csv"
    )
    bot = RealTimeBot(source, mode="backtest")

    # Bot temps réel
    # source = CandleSourceBinance(symbol="ethusdc", interval="1m", warmup_count=1)
    # bot = RealTimeBot(source, warmup_count=1, mode="realtime")
    # asyncio.run(bot.start())
