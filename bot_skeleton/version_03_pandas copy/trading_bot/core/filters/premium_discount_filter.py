import pandas as pd

class PremiumDiscountFilter:
    def __init__(self, df: pd.DataFrame, window: int = 20):
        """
        df : DataFrame avec au moins ['signal','close','high','low']
        signal_col : nom de la colonne des signaux
        window : nombre de bougies pour calculer les zones
        """
        self.df = df.copy()
        self.signal_col = 'signal'
        self.window = window

    def apply_filter(self):
        # Conserver le signal original
        self.df['original_signal'] = self.df[self.signal_col]

        # Calculer le max et le min sur la fenêtre historique
        swing_high = self.df['high'].rolling(self.window, min_periods=1).max()
        swing_low = self.df['low'].rolling(self.window, min_periods=1).min()

        # Calculer le centre de la zone
        zone_center = (swing_high + swing_low) / 2

        # Définir une colonne indiquant la zone du prix
        self.df['zone'] = ['premium' if price > zone_center.iloc[i] else 'discount'
                   for i, price in enumerate(self.df['close'])]

        # Filtrer les signaux
        buy_mask = (self.df[self.signal_col] == 'BUY') & (self.df['zone'] == 'premium')
        self.df.loc[buy_mask, self.signal_col] = None

        sell_mask = (self.df[self.signal_col] == 'SELL') & (self.df['zone'] == 'discount')
        self.df.loc[sell_mask, self.signal_col] = None

        return self.df
