import pandas as pd

class EmaTrendFilter:
    def __init__(self, df: pd.DataFrame, ema_col: str = "ema_21"):
        """
        df : DataFrame contenant au moins ['signal','close'] et la colonne EMA
        ema_col : nom de la colonne EMA
        signal_col : nom de la colonne des signaux
        """
        self.df = df.copy()
        self.ema_col = ema_col
        self.signal_col = "signal"

    def apply_filter(self):
        # Créer la colonne original_signal pour conserver le signal d'origine
        self.df['original_signal'] = self.df[self.signal_col]

        # Filtrer les BUY sous l'EMA
        buy_mask = (self.df[self.signal_col] == 'BUY') & (self.df['close'] < self.df[self.ema_col])
        self.df.loc[buy_mask, self.signal_col] = None

        # Filtrer les SELL au-dessus de l'EMA
        sell_mask = (self.df[self.signal_col] == 'SELL') & (self.df['close'] > self.df[self.ema_col])
        self.df.loc[sell_mask, self.signal_col] = None

        return self.df
