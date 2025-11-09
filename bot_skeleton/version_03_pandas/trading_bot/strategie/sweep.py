import pandas as pd

class SweepStrategy:
    def __init__(self, df: pd.DataFrame):
        """
        df : DataFrame contenant au moins ['close','sweep_high','sweep_low', ema_column]
        ema_column : nom de la colonne EMA21
        """
        self.df = df

    def generate_signals(self):
        signals = []

        for i in range(len(self.df)):
            row = self.df.iloc[i]
            signal = None

            # Pour la première bougie, on ne peut pas comparer EMA
            if i == 0:
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
