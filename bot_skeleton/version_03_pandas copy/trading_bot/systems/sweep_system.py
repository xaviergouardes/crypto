from typing import override
import pandas as pd
import numpy as np

from trading_bot.systems.system_abstract import System

from trading_bot.core.indicators.ema import Ema
from trading_bot.core.indicators.swing_detector import SwingDetector
from trading_bot.core.indicators.sweep_detector import SweepDetector

from trading_bot.core.signal_generators.sweep import SweepSignalGenerator

from trading_bot.core.risk_managers.risk_manager import RiskManager
from trading_bot.core.trader.trader_only_one_position import OnlyOnePositionTrader

from trading_bot.reporting.portefolio import Portfolio

from trading_bot.reporting.statistiques import Statistiques

class SweepSystem(System):

    def __init__(self, params):
        self.params = params
        self.signal_generator = SweepSignalGenerator()

    @override
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.params

        df = df.copy()

        # Exemple simple avec tous les indicateurs et stratégie

        df = Ema(df).add_ema(p["ema_fast"])
        df = Ema(df).add_ema(p["ema_slow"])
        df = SwingDetector(df, window=p["swing_window"], side=p["swing_side"]).detect()
        df = SweepDetector(df).detect()

        df = self.signal_generator.generate_signals(df)
 
        # wick_filter = WickFilter(df)
        # df = wick_filter.apply_filter()

        df = RiskManager(df, tp_pct=p["tp_pct"], sl_pct=p["tp_pct"]).calculate_risk()
        df = OnlyOnePositionTrader(df).run_trades()

        df = Portfolio(df, initial_capital=p["initial_capital"]).run_portfolio()

        stats = Statistiques(df, initial_capital=p["initial_capital"])
                
        return df, stats