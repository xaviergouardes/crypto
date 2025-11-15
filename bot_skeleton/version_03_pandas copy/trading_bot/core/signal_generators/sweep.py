import pandas as pd
import numpy as np

class SweepSignalGenerator:

    def generate_signals(self, df: pd.DataFrame):
        # Copie pour éviter les effets de bord
        df_with_signals = df.copy()

        # Par sécurité : convertir en booléen ou NaN
        df_with_signals['sweep_high'] = df_with_signals['sweep_high'].where(df_with_signals['sweep_high'].notna(), np.nan)
        df_with_signals['sweep_low'] = df_with_signals['sweep_low'].where(df_with_signals['sweep_low'].notna(), np.nan)

        # Conditions logiques
        cond_sell = df_with_signals['sweep_high'] == True
        cond_buy = df_with_signals['sweep_low'] == True
        cond_nan = df_with_signals['sweep_high'].isna() | df_with_signals['sweep_low'].isna()
        cond_conflict = cond_sell & cond_buy  # Les deux détectés en même temps

        # Attribution vectorisée
        df_with_signals['signal'] = np.select(
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

        return df_with_signals
