import pandas as pd

from trading_bot.data_market.candel_snapshot_csv import CandelSnapshotCsv

from trading_bot.indicator.ema import Ema
from trading_bot.indicator.swing_detector import SwingDetector
from trading_bot.indicator.sweep_detector import SweepDetector

from trading_bot.strategie.sweep import SweepStrategy

from trading_bot.filter.ema_trend_filter import EmaTrendFilter
from trading_bot.filter.premium_discount_filter import PremiumDiscountFilter
from trading_bot.filter.wick_filter import WickFilter

from trading_bot.risk_manager.risk_manager import RiskManager

from trading_bot.trader.trader_only_one_position import OnlyOnePositionTrader

from trading_bot.journal.portefolio import Portfolio
from trading_bot.journal.statistiques import Statistiques

if __name__ == "__main__":
    path = "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250901_20251104.csv"

    data = CandelSnapshotCsv(path)
    df = data.load()

    ema_computer = Ema(df)
    df = ema_computer.add_ema(21)
    df = ema_computer.add_ema(7)

    swings_detector = SwingDetector(df, window=100, side=2)
    df = swings_detector.detect()

    sweep_detector = SweepDetector(df)
    df = sweep_detector.detect()

    sweep_strategy = SweepStrategy(df)
    df = sweep_strategy.generate_signals()

    # ema_trend_filter = EmaTrendFilter(df, ema_col="ema_7")
    # df = ema_trend_filter.apply_filter()

    # premium_discount_filter = PremiumDiscountFilter(df, window=100)
    # df = premium_discount_filter.apply_filter()

    # wick_filter = WickFilter(df)
    # df = wick_filter.apply_filter()

    # risk_manager = RiskManager(df, tp_pct=1.0, sl_pct=0.6)
    # df = risk_manager.calculate_risk()

    # trader = OnlyOnePositionTrader(df)
    # df = trader.run_trades()

    # portefolio = Portfolio(df, initial_capital=1000)
    # df = portefolio.run_portfolio()

    # stats = Statistiques(df, initial_capital=1000)
    # print(stats.summary())


    # print(list(df.columns)) # affiche une vraie liste Python
    pd.set_option('display.max_rows', None)

    # sweeps = df[(df['sweep_high'] == True) | (df['sweep_low'] == True)]
    filtered_df = df[df['signal'].notna()]
    print(filtered_df[['timestamp_paris', 'open', 'high', 'low', 'close', 'swing_high', 'swing_low', 'sweep_high', 'sweep_low', 'signal']])
    # print(filtered_df[['timestamp_paris', 'close', 'signal', 'entry_price', 'tp', 'sl', 'tp_pct', 'sl_pct']])


    # filtered_df = df[df['position'].isin(["CLOSE_BUY_TP", "CLOSE_SELL_TP", "CLOSE_BUY_SL", "CLOSE_SELL_SL"]) ]
    # filtered_df = df[df['trade_id'].isin((1,2,3))]
    # filtered_df = df[df['trade_id'] == 22]
    # print(filtered_df[['timestamp_paris', 'close', 'signal', 'entry_price', 'tp', 'sl', 'position', 'capital', 'trade_pnl', 'trade_id']])
          

    # filtered_df = df[df['original_signal'].notna() & df['signal'].isna()]
    # print(filtered_df[['timestamp_paris', 'close', 'signal', 'original_signal', 'entry_price', 'zone']])
    # print(filtered_df[['timestamp_paris', 'close', 'signal', 'entry_price', 'tp', 'sl', 'tp_pct', 'sl_pct', 'position', 'trade_id']])

    # print(stats.summary())