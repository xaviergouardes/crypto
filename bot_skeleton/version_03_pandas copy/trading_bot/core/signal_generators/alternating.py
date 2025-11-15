import pandas as pd

class RandomAlternatingStrategy:
    """
    Génère des signaux BUY / SELL selon la minute du timestamp.
    Les conditions sont mutuellement exclusives :
    - SELL : minute multiple de 3 mais pas de 5
    - BUY  : minute multiple de 5 mais pas de 3
    - None : sinon
    """

    def generate_signals(self, df: pd.DataFrame, warmup_count):
        signals = []

        for i in range(len(df)):

            if i < warmup_count:
                signals.append(None)
                continue

            timestamp = df.at[i, 'timestamp']
            minute = timestamp.minute
            signal = None

            if minute % 3 == 0 and minute % 5 != 0:
                signal = 'SELL'
            elif minute % 5 == 0 and minute % 3 != 0:
                signal = 'BUY'

            signals.append(signal)

        df['signal'] = signals
        return df
