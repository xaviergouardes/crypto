import pandas as pd

class Portfolio:
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital

    def run_portfolio(self, df: pd.DataFrame) -> pd.DataFrame:
        working_df = df.copy()

        capital = self.initial_capital
        trade_pnl_list = []
        capital_list = []

        for i, row in working_df.iterrows():
            pos = row['position']
            entry = row['trade.entry_price']
            close = row['close']

            trade_pnl = 0.0

            if pos is not None:
                # BUY
                if pos.startswith('CLOSE_BUY'):
                    trade_pnl = capital * (close - entry) / entry
                    # Si fermé sur SL → négatif garanti
                    if pos.endswith('_SL') and trade_pnl > 0:
                        trade_pnl = -abs(trade_pnl)
                    # Si fermé sur TP → positif garanti
                    elif pos.endswith('_TP') and trade_pnl < 0:
                        trade_pnl = abs(trade_pnl)

                # SELL
                elif pos.startswith('CLOSE_SELL'):
                    trade_pnl = capital * (entry - close) / entry
                    # SL → négatif
                    if pos.endswith('_SL') and trade_pnl > 0:
                        trade_pnl = -abs(trade_pnl)
                    # TP → positif
                    elif pos.endswith('_TP') and trade_pnl < 0:
                        trade_pnl = abs(trade_pnl)

                capital += trade_pnl

            trade_pnl_list.append(trade_pnl)
            capital_list.append(capital)

        working_df['trade_pnl'] = trade_pnl_list
        working_df['capital'] = capital_list

        return working_df
