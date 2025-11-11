import pandas as pd
import numpy as np

class SweepStrategy:
    def __init__(self, df: pd.DataFrame):
        """
        df : DataFrame contenant au moins ['close','sweep_high','sweep_low']
        """
        self.df = df

    def generate_signals(self):
        signals = []

        for i in range(len(self.df)):
            row = self.df.iloc[i]
            signal = None

            # On ne peut pas évaluer si l'un des deux swings est manquant
            if pd.isna(row.get('sweep_high')) or pd.isna(row.get('sweep_low')):
                signals.append(None)
                continue

            # Sweep high → potentiel SELL
            if row['sweep_high']:
                signal = 'SELL'

            # Sweep low → potentiel BUY
            if row['sweep_low']:
                signal = 'BUY'

            signals.append(signal)

        self.df['signal'] = signals
        return self.df
