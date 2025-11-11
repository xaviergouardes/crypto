import pandas as pd

class RandomAlternatingStrategy:
    """
    Génère des signaux BUY / SELL selon la minute du timestamp.
    Les conditions sont mutuellement exclusives :
    - SELL : minute multiple de 3 mais pas de 5
    - BUY  : minute multiple de 5 mais pas de 3
    - None : sinon
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def generate_signals(self):
        signals = []

        for i in range(len(self.df)):
            timestamp = self.df.at[i, 'timestamp']
            minute = timestamp.minute
            signal = None

            if minute % 3 == 0 and minute % 5 != 0:
                signal = 'SELL'
            elif minute % 5 == 0 and minute % 3 != 0:
                signal = 'BUY'

            signals.append(signal)

        self.df['signal'] = signals
        return self.df
