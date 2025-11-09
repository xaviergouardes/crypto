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
        Retourne deux listes : swing_highs (valeurs des high) et swing_lows (valeurs des low)
        détectées à l'intérieur de la fenêtre wdf en appliquant la condition 'side' de chaque côté.
        """
        highs = wdf['high'].values
        lows = wdf['low'].values
        n = len(wdf)

        swing_highs = []
        swing_lows = []

        # indices relatifs dans la fenêtre où on peut détecter un swing local
        for j in range(self.side, n - self.side):
            left_highs = highs[j - self.side:j]
            right_highs = highs[j+1:j+1+self.side]
            left_lows = lows[j - self.side:j]
            right_lows = lows[j+1:j+1+self.side]

            # swing high local : high strictement > tous les voisins de chaque côté
            if highs[j] > left_highs.max() and highs[j] > right_highs.max():
                swing_highs.append(highs[j])

            # swing low local : low strictement < tous les voisins de chaque côté
            if lows[j] < left_lows.min() and lows[j] < right_lows.min():
                swing_lows.append(lows[j])

        return swing_highs, swing_lows

    def detect(self, output_nan=True):
        """
        Parcourt le DataFrame et ajoute deux colonnes :
            - 'swing_high' : la valeur du max swing high trouvée dans la fenêtre terminée à t,
                              ou None/NaN si aucun swing ou si cassure par le prix courant.
            - 'swing_low'  : la valeur du min swing low trouvée dans la fenêtre terminée à t,
                              ou None/NaN si aucun swing ou si cassure par le prix courant.

        output_nan : si True -> utilise np.nan, sinon -> utilise None.
        """
        n = len(self.df)
        swing_high_col = [np.nan] * n
        swing_low_col = [np.nan] * n
        use_nan = bool(output_nan)

        for idx in range(n):
            # début de fenêtre (inclus)
            start = idx - self.window + 1
            if start < 0:
                # pas assez d'historique -> laisser NaN/None
                swing_high_col[idx] = np.nan if use_nan else None
                swing_low_col[idx] = np.nan if use_nan else None
                continue

            wdf = self.df.iloc[start: idx + 1]  # fenêtre qui termine sur idx (incluse)
            # si la fenêtre est trop petite pour détecter local swings, on passe
            if len(wdf) < (2 * self.side + 1):
                swing_high_col[idx] = np.nan if use_nan else None
                swing_low_col[idx] = np.nan if use_nan else None
                continue

            # repérer tous les swings locaux dans la fenêtre
            found_highs, found_lows = self._find_swings_in_window(wdf)

            # prendre le max pour swing_high et min pour swing_low si présents
            max_swing_high = max(found_highs) if len(found_highs) > 0 else None
            min_swing_low = min(found_lows) if len(found_lows) > 0 else None

            current_close = self.df['close'].iat[idx]

            # Si le prix courant casse le max swing high on considère qu'il est invalidé -> None/NaN
            if max_swing_high is not None and current_close > max_swing_high:
                max_swing_high = None

            # Pareil pour le swing low : si le prix courant casse par le bas (< min) -> None
            if min_swing_low is not None and current_close < min_swing_low:
                min_swing_low = None

            swing_high_col[idx] = max_swing_high if max_swing_high is not None else (np.nan if use_nan else None)
            swing_low_col[idx] = min_swing_low if min_swing_low is not None else (np.nan if use_nan else None)

        # Ajout au df principal
        self.df['swing_high'] = swing_high_col
        self.df['swing_low'] = swing_low_col

        return self.df
