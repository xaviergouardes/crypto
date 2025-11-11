import pandas as pd
import numpy as np

class SwingDetector:
    def __init__(self, df: pd.DataFrame, window: int = 20, side: int = 2):
        """
        df : DataFrame contenant au moins ['high','low','close'] et index temporel.
        window : nombre de bougies historiques à regarder (fenêtre glissante).
        side : nombre de bougies de chaque côté pour définir localement un swing (ex: 2).
               La détection locale d'un swing nécessite au moins (2*side + 1) bougies.
        """
        if window < (2 * side + 1):
            raise ValueError("window doit être >= 2*side+1 pour permettre la détection locale des swings.")
        if side < 1:
            raise ValueError("side doit être >= 1")
        self.df = df
        self.window = int(window)
        self.side = int(side)

    def _find_swings_in_window(self, wdf: pd.DataFrame):
        """
        Retourne deux listes : swing_highs et swing_lows détectés à l'intérieur de la fenêtre wdf.
        """
        highs = wdf['high'].values
        lows = wdf['low'].values
        n = len(wdf)

        swing_highs = []
        swing_lows = []

        for j in range(self.side, n - self.side):
            left_highs = highs[j - self.side:j]
            right_highs = highs[j+1:j+1+self.side]
            left_lows = lows[j - self.side:j]
            right_lows = lows[j+1:j+1+self.side]

            # swing high local : high strictement > tous les voisins
            if highs[j] > left_highs.max() and highs[j] > right_highs.max():
                swing_highs.append(highs[j])

            # swing low local : low strictement < tous les voisins
            if lows[j] < left_lows.min() and lows[j] < right_lows.min():
                swing_lows.append(lows[j])

        return swing_highs, swing_lows

    def detect(self, output_nan=True):
        """
        Parcourt le DataFrame et ajoute deux colonnes :
            - 'swing_high' : max swing high de la fenêtre si le prix courant reste dans le range
            - 'swing_low'  : min swing low de la fenêtre si le prix courant reste dans le range
        Si le prix courant sort du range, aucune détection n'est faite.
        """
        n = len(self.df)
        swing_high_col = [np.nan] * n
        swing_low_col = [np.nan] * n
        use_nan = bool(output_nan)

        for idx in range(n):
            start = idx - self.window + 1
            if start < 0:
                swing_high_col[idx] = np.nan if use_nan else None
                swing_low_col[idx] = np.nan if use_nan else None
                continue

            wdf = self.df.iloc[start: idx + 1]
            if len(wdf) < (2 * self.side + 1):
                swing_high_col[idx] = np.nan if use_nan else None
                swing_low_col[idx] = np.nan if use_nan else None
                continue

            # repérer tous les swings locaux dans la fenêtre
            found_highs, found_lows = self._find_swings_in_window(wdf)

            if not found_highs or not found_lows:
                # pas de swings détectés
                swing_high_col[idx] = np.nan if use_nan else None
                swing_low_col[idx] = np.nan if use_nan else None
                continue

            # max swing high et min swing low de la fenêtre
            max_swing_high = max(found_highs)
            min_swing_low = min(found_lows)

            current_close = self.df['close'].iat[idx]

            # Condition stricte : si le prix courant sort du range [min_swing_low, max_swing_high], aucun swing
            if current_close > max_swing_high or current_close < min_swing_low:
                max_swing_high = None
                min_swing_low = None

            swing_high_col[idx] = max_swing_high if max_swing_high is not None else (np.nan if use_nan else None)
            swing_low_col[idx] = min_swing_low if min_swing_low is not None else (np.nan if use_nan else None)

        self.df['swing_high'] = swing_high_col
        self.df['swing_low'] = swing_low_col
        return self.df
