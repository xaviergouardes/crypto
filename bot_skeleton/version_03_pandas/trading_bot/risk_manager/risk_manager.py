import pandas as pd

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
        last_entry = None
        last_tp = None
        last_sl = None
        last_tp_pct = None
        last_sl_pct = None

        entry_price = []
        tp = []
        sl = []
        tp_pct = []
        sl_pct = []

        for _, row in self.df.iterrows():
            sig = row['signal']
            price = row['close']

            if sig == 'BUY':
                last_entry = price
                last_tp = price * (1 + self.tp_ratio)
                last_sl = price * (1 - self.sl_ratio)
                last_tp_pct = self.tp_ratio * 100
                last_sl_pct = self.sl_ratio * 100

            elif sig == 'SELL':
                last_entry = price
                last_tp = price * (1 - self.tp_ratio)
                last_sl = price * (1 + self.sl_ratio)
                last_tp_pct = self.tp_ratio * 100
                last_sl_pct = self.sl_ratio * 100

            # Ajouter les dernières valeurs même si pas de signal
            entry_price.append(last_entry)
            tp.append(last_tp)
            sl.append(last_sl)
            tp_pct.append(last_tp_pct)
            sl_pct.append(last_sl_pct)

        self.df['entry_price'] = entry_price
        self.df['tp'] = tp
        self.df['sl'] = sl
        self.df['tp_pct'] = tp_pct
        self.df['sl_pct'] = sl_pct

        return self.df
