import pandas as pd

class Ema:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def add_ema(self, span=21):
        self.df[f'ema_{span}'] = self.df['close'].ewm(span=span, adjust=False).mean()
        return self.df