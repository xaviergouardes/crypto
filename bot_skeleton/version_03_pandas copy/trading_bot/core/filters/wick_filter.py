import pandas as pd

class WickFilter:
    def __init__(self, df: pd.DataFrame):
        """
        df : DataFrame contenant au moins ['signal', 'open', 'high', 'low', 'close']
        """
        self.df = df.copy()
        self.signal_col = "signal"

    def _compute_wick_features(self):
        """Ajoute des colonnes booléennes décrivant les mèches et la direction."""
        o, h, l, c = self.df['open'], self.df['high'], self.df['low'], self.df['close']
        total_size = h - l

        # Éviter les divisions par 0
        total_size = total_size.replace(0, 1e-9)

        self.df['upper_wick'] = h - c.where(c > o, o)
        self.df['lower_wick'] = o.where(c > o, c) - l

        self.df['bearish'] = c < o
        self.df['bullish'] = c > o

        self.df['bearish_wick'] = self.df['upper_wick'] >= total_size / 3
        self.df['bullish_wick'] = self.df['lower_wick'] >= total_size / 3

    def apply_filter(self):
        """
        Filtre les signaux selon la mèche et le type de bougie.
        Règles :
        - Signal BUY => conservé SEULEMENT si bougie bullish avec mèche basse ≥ 1/3
        - Signal SELL => conservé SEULEMENT si bougie bearish avec mèche haute ≥ 1/3
        """
        # Sauvegarde des signaux d’origine
        self.df['original_signal'] = self.df[self.signal_col]

        # Calcul des caractéristiques de mèche
        self._compute_wick_features()

        # --- Application du filtre ---

        # Filtrage des BUY (supprime ceux qui ne respectent pas les conditions)
        invalid_buy = ~(
            (self.df['signal'] == 'BUY')
            & self.df['bullish']
            & self.df['bullish_wick']
        )

        # Filtrage des SELL (supprime ceux qui ne respectent pas les conditions)
        invalid_sell = ~(
            (self.df['signal'] == 'SELL')
            & self.df['bearish']
            & self.df['bearish_wick']
        )

        # Mise à None des signaux invalides
        self.df.loc[invalid_buy & (self.df['signal'] == 'BUY'), self.signal_col] = None
        self.df.loc[invalid_sell & (self.df['signal'] == 'SELL'), self.signal_col] = None

        return self.df
