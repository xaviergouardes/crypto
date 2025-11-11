import pandas as pd

class OnlyOnePositionTrader:
    def __init__(self, df: pd.DataFrame):
        """
        df : DataFrame contenant au moins ['signal','close','high','low','entry_price','tp','sl']
        TP et SL doivent déjà être calculés par le RiskManager
        """
        self.df = df.copy()

    def run_trades(self):
        position = None
        trade_counter = 0

        # Listes pour remplir le DataFrame
        position_list = []
        trade_id_list = []

        # Parcours des lignes
        for i, row in self.df.iterrows():
            sig = row['signal']
            close = row['close']
            high = row['high']
            low = row['low']

            entry_price = row['entry_price']
            tp_price = row['tp']
            sl_price = row['sl']

            # Si une position est ouverte
            if position == 'BUY':
                if low <= sl_price <= high:
                    position_list.append('CLOSE_BUY_SL')
                    position = None
                elif low <= tp_price <= high:
                    position_list.append('CLOSE_BUY_TP')
                    position = None
                else:
                    position_list.append('OPEN_BUY')

                trade_id_list.append(trade_counter)

            elif position == 'SELL':
                if low <= tp_price <= high:
                    position_list.append('CLOSE_SELL_TP')
                    position = None
                elif low <= sl_price <= high:
                    position_list.append('CLOSE_SELL_SL')
                    position = None
                else:
                    position_list.append('OPEN_SELL')

                trade_id_list.append(trade_counter)

            # Si aucune position ouverte, ouvrir selon signal
            elif position is None and sig in ['BUY', 'SELL']:
                trade_counter += 1
                position = sig
                if sig == 'BUY':
                    position_list.append('OPEN_BUY')
                else:
                    position_list.append('OPEN_SELL')

                trade_id_list.append(trade_counter)

            # Pas de position ni signal
            else:
                position_list.append(None)
                trade_id_list.append(None)

        # Création des colonnes
        self.df['position'] = position_list
        self.df['trade_id'] = trade_id_list

        # Propagation des valeurs entry_price, tp, sl sur toutes les lignes du trade
        cols_to_propagate = ['entry_price', 'tp', 'sl']
        self.df['trade_id'] = self.df['trade_id'].astype(float)
        for col in cols_to_propagate:
            self.df[col] = self.df.groupby('trade_id')[col].transform(lambda x: x.ffill().bfill())

        return self.df
