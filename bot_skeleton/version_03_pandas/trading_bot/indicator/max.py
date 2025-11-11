import pandas as pd

class Max:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def add_max(self, span=21):
        self.df[f'max_{span}'] = self.df['high'].rolling(window=span, min_periods=1).max()
        return self.df