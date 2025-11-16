import pandas as pd
import numpy as np

class SweepDetector:
    def __init__(self, df: pd.DataFrame):
        """
        df : DataFrame contenant au moins les colonnes ['open','high','low','close','last_swing_high','last_swing_low']
        """
        self.df = df.copy()

    def detect(self):
        df = self.df

        # Conditions Sweep High
        cond_sh = (
            df['last_swing_high'].notna() &
            (df['close'] < df['open']) &
            (df['open'] < df['last_swing_high']) &
            (df['last_swing_high'] < df['high'])
        )

        # Conditions Sweep Low
        cond_sl = (
            df['last_swing_low'].notna() &
            (df['close'] > df['open']) &
            (df['low'] < df['last_swing_low']) &
            (df['last_swing_low'] < df['open'])
        )

        # Assignation vectorisée
        df['sweep_high'] = cond_sh
        df['sweep_low'] = cond_sl

        self.df = df
        return self.df
