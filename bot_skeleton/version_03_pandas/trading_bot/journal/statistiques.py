import pandas as pd
import numpy as np

class Statistiques:
    REQUIRED_COLUMNS = ['position', 'entry_price', 'close']

    def __init__(self, df: pd.DataFrame, initial_capital: float = 1000.0):
        """
        df : DataFrame contenant au moins ['position', 'entry_price', 'close']
        initial_capital : solde initial en USDC
        """
        # Vérification des colonnes essentielles
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Le DataFrame ne contient pas les colonnes nécessaires pour calculer les statistiques : {missing_cols}")

        self.df = df.copy()
        self.initial_capital = initial_capital

        # Si la colonne trade_pnl n’existe pas, on la calcule
        if 'trade_pnl' not in self.df.columns:
            self.df['trade_pnl'] = self.df.apply(
                lambda row: (row['close'] - row['entry_price'])
                if row['position'] == 'long'
                else (row['entry_price'] - row['close'])
                if row['position'] == 'short'
                else 0,
                axis=1
            )

        # Calcul initial de la courbe d'équité
        self.df['equity'] = self.initial_capital + self.df['trade_pnl'].cumsum()

    # --- Métriques principales ---
    def compute_win_rate(self) -> float:
        wins = (self.df['trade_pnl'] > 0).sum()
        total = (self.df['trade_pnl'] != 0).sum()
        return round((wins / total * 100), 2) if total > 0 else 0.0

    def compute_equity_curve(self) -> pd.Series:
        return self.df['equity']

    def compute_max_min_balance(self) -> tuple:
        return self.df['equity'].max(), self.df['equity'].min()

    def compute_profit_factor(self) -> float:
        gains = self.df.loc[self.df['trade_pnl'] > 0, 'trade_pnl'].sum()
        losses = self.df.loc[self.df['trade_pnl'] < 0, 'trade_pnl'].sum()
        if losses == 0:
            return np.inf
        return round(abs(gains / losses), 2)

    def compute_max_drawdown(self) -> float:
        equity = self.df['equity']
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_dd = drawdown.min() * 100
        return round(max_dd, 2)

    def compute_average_pnl(self) -> float:
        valid_trades = self.df[self.df['trade_pnl'] != 0]['trade_pnl'].dropna()
        if valid_trades.empty:
            return 0.0
        return round(valid_trades.mean(), 4)

    def compute_pnl_stats(self):
        valid_trades = self.df[self.df['trade_pnl'] != 0]['trade_pnl'].dropna()
        if valid_trades.empty:
            return {"average": 0.0, "average_win": 0.0, "average_loss": 0.0}
        wins = valid_trades[valid_trades > 0]
        losses = valid_trades[valid_trades < 0]
        return {
            "average": round(valid_trades.mean(), 4),
            "average_win": round(wins.mean(), 4) if not wins.empty else 0.0,
            "average_loss": round(losses.mean(), 4) if not losses.empty else 0.0,
        }

    def summary(self) -> pd.DataFrame:
        win_rate = self.compute_win_rate()
        max_balance, min_balance = self.compute_max_min_balance()
        last_equity = self.df['equity'].iloc[-1]
        profit_factor = self.compute_profit_factor()
        max_drawdown = self.compute_max_drawdown()
        avg_pnl = self.compute_average_pnl()

        data = {
            'Nb trades': [(self.df['trade_pnl'] != 0).sum()],
            'Win rate (%)': [win_rate],
            'Profit factor': [profit_factor],
            'PNL moyen': [avg_pnl],
            'Max drawdown (%)': [max_drawdown],
            'Solde final': [round(last_equity, 2)],
            'Solde max': [round(max_balance, 2)],
            'Solde min': [round(min_balance, 2)],
        }
        return pd.DataFrame(data)
