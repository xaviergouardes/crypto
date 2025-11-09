import pandas as pd

class Portfolio:
    def __init__(self, df: pd.DataFrame, initial_capital: float = 1000.0):
        """
        df : DataFrame contenant au moins ['position','entry_price','close']
        initial_capital : solde initial en USDC
        """
        self.df = df
        self.initial_capital = initial_capital

    def run_portfolio(self):
        capital = self.initial_capital
        trade_pnl_list = []
        capital_list = []

        for i, row in self.df.iterrows():
            pos = row['position']
            entry = row['entry_price']
            close = row['close']

            trade_pnl = 0.0

            # Calcul PnL uniquement si trade fermé
            if pos in ['CLOSE_BUY_TP','CLOSE_BUY_SL']:
                trade_pnl = capital * (close - entry) / entry
                capital += trade_pnl

            elif pos in ['CLOSE_SELL_TP','CLOSE_SELL_SL']:
                trade_pnl = capital * (entry - close) / entry
                capital += trade_pnl

            trade_pnl_list.append(trade_pnl)
            capital_list.append(capital)

        self.df['trade_pnl'] = trade_pnl_list
        self.df['capital'] = capital_list

        return self.df
