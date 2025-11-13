import pandas as pd
import numpy as np

class SweepStrategy:
    def __init__(self, df: pd.DataFrame):
        """
        df : DataFrame contenant au moins ['close','sweep_high','sweep_low']
        """
        self.df = df

    def generate_signals(self):
        # Copie pour éviter les effets de bord
        df = self.df.copy()

        # Par sécurité : convertir en booléen ou NaN
        df['sweep_high'] = df['sweep_high'].where(df['sweep_high'].notna(), np.nan)
        df['sweep_low'] = df['sweep_low'].where(df['sweep_low'].notna(), np.nan)

        # Conditions logiques
        cond_sell = df['sweep_high'] == True
        cond_buy = df['sweep_low'] == True
        cond_nan = df['sweep_high'].isna() | df['sweep_low'].isna()
        cond_conflict = cond_sell & cond_buy  # Les deux détectés en même temps

        # Attribution vectorisée
        df['signal'] = np.select(
            condlist=[
                cond_conflict,
                cond_nan,
                cond_sell,
                cond_buy
            ],
            choicelist=[
                'CONFLICT',
                None,
                'SELL',
                'BUY'
            ],
            default=None
        )

        self.df = df
        return df
