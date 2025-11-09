import pandas as pd

class SweepDetector:
    def __init__(self, df: pd.DataFrame):
        """
        df : DataFrame contenant au moins les colonnes ['open','high','low','close','swing_high','swing_low']
        """
        self.df = df

    def detect(self):
        sweep_high = []
        sweep_low = []

        for i, row in self.df.iterrows():
            sh = row['swing_high']
            sl = row['swing_low']

            # Sweep High : bougie bearish et la meche haute dépasse le swing high
            if not pd.isna(sh) and row['close'] < row['open'] and row['open'] < sh < row['high']:
                sweep_high.append(True)
            else:
                sweep_high.append(False)

            # Sweep Low : bougie bullish et la meche basse dépasse le swing low
            if not pd.isna(sl) and row['close'] > row['open'] and row['low'] < sl < row['close']:
                sweep_low.append(True)
            else:
                sweep_low.append(False)

        self.df['sweep_high'] = sweep_high
        self.df['sweep_low'] = sweep_low

        return self.df
