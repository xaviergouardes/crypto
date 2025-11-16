import pandas as pd
import numpy as np

class SwingDetector:
    def __init__(self, df: pd.DataFrame, window: int = 100, side: int = 2):
        self.df = df.copy()
        self.window = window
        self.side = side

    def detect(self):
        df = self.df
        side = self.side

        # Étape 1 : Détection des swings (vectorielle)
        df['is_swing_high'] = True
        df['is_swing_low'] = True

        for i in range(1, side+1):
            df['is_swing_high'] &= df['high'] > df['high'].shift(i)
            df['is_swing_high'] &= df['high'] > df['high'].shift(-i)
            
            df['is_swing_low'] &= df['low'] < df['low'].shift(i)
            df['is_swing_low'] &= df['low'] < df['low'].shift(-i)

        df['swing_high_value'] = np.where(df['is_swing_high'], df['high'], np.nan)
        df['swing_low_value']  = np.where(df['is_swing_low'], df['low'], np.nan)

        # Étape 2 : Calcul du max/min dans la fenêtre glissante en excluant les side bougies aux bords
        def max_exclude_edges(x):
            if len(x) <= 2*side:
                return np.nan
            center = x[side:-side]
            return np.nanmax(center) if np.any(~np.isnan(center)) else np.nan

        def min_exclude_edges(x):
            if len(x) <= 2*side:
                return np.nan
            center = x[side:-side]
            return np.nanmin(center) if np.any(~np.isnan(center)) else np.nan

        df['last_swing_high'] = df['swing_high_value'].rolling(self.window, min_periods=1).apply(max_exclude_edges, raw=True)
        df['last_swing_low']  = df['swing_low_value'].rolling(self.window, min_periods=1).apply(min_exclude_edges, raw=True)

        self.df = df

        # filtred = self.df.head(200)
        # # filtred = df[df['high'] == df['rolling_max']]
        # # filtred = df[df['is_swing_low'] == True]
        # filtred = self.df.query("index >= 780 and index < 900")
        # pd.set_option('display.max_rows', None)
        # print(filtred[['timestamp_paris', 'high', 'low','is_swing_high', 'is_swing_low', 'last_swing_high', 'last_swing_low']].head(300))

        # # print(filtred[['timestamp_paris', 'high', 'low', 'is_swing_high', 'is_swing_low']].head(300))

        # raise Exception()

        return self.df
 



