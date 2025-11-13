import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self, df: pd.DataFrame, tp_pct: float = 1.2, sl_pct: float = 0.6):
        """
        df : DataFrame contenant au moins ['close','signal']
        tp_pct/sl_pct : pourcentages de TP et SL
        """
        self.df = df.copy()
        self.tp_ratio = tp_pct / 100
        self.sl_ratio = sl_pct / 100

    def calculate_risk(self):
        df = self.df

        # Initialisation avec NaN
        df['entry_price'] = np.nan
        df['tp'] = np.nan
        df['sl'] = np.nan
        df['tp_pct'] = np.nan
        df['sl_pct'] = np.nan

        # Calcul vectoriel avec np.where
        df['entry_price'] = np.where(df['signal'].isin(['BUY','SELL']), df['close'], np.nan)
        df['tp'] = np.where(df['signal'] == 'BUY', df['close'] * (1 + self.tp_ratio),
                            np.where(df['signal'] == 'SELL', df['close'] * (1 - self.tp_ratio), np.nan))
        df['sl'] = np.where(df['signal'] == 'BUY', df['close'] * (1 - self.sl_ratio),
                            np.where(df['signal'] == 'SELL', df['close'] * (1 + self.sl_ratio), np.nan))
        df['tp_pct'] = np.where(df['signal'].isin(['BUY','SELL']), self.tp_ratio * 100, np.nan)
        df['sl_pct'] = np.where(df['signal'].isin(['BUY','SELL']), self.sl_ratio * 100, np.nan)

        # Forward fill pour propager les dernières valeurs
        df[['entry_price','tp','sl','tp_pct','sl_pct']] = df[['entry_price','tp','sl','tp_pct','sl_pct']].ffill()

        self.df = df
        return df
