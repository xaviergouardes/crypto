import pandas as pd

class RiskManager:
    def __init__(self, df: pd.DataFrame, tp_pct: float = 1.2, sl_pct: float = 0.6):
        """
        df : DataFrame contenant au moins ['close','signal']
        tp_pct : Take profit en pourcentage (ex: 2 = 2%)
        sl_pct : Stop loss en pourcentage (ex: 1 = 1%)
        """
        self.df = df
        # Convertir en ratio pour le calcul
        self.tp_ratio = tp_pct / 100
        self.sl_ratio = sl_pct / 100

    def calculate_risk(self):
        entry_price = []
        tp = []
        sl = []

        for i, row in self.df.iterrows():
            sig = row['signal']
            close_price = row['close']

            if sig == 'BUY':
                entry = close_price
                entry_price.append(entry)
                tp.append(entry * (1 + self.tp_ratio))  # TP au-dessus
                sl.append(entry * (1 - self.sl_ratio))  # SL en dessous
            elif sig == 'SELL':
                entry = close_price
                entry_price.append(entry)
                tp.append(entry * (1 - self.tp_ratio))  # TP en dessous
                sl.append(entry * (1 + self.sl_ratio))  # SL au-dessus
            else:
                entry_price.append(None)
                tp.append(None)
                sl.append(None)

        self.df['entry_price'] = entry_price
        self.df['tp'] = tp
        self.df['sl'] = sl

        return self.df
