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

        # Colonnes figées pour TP/SL et entry_price
        trade_entry_price_list = []
        trade_tp_list = []
        trade_sl_list = []

        # Valeurs figées du trade en cours
        trade_entry_price = None
        trade_tp = None
        trade_sl = None

        # Parcours des lignes
        for i, row in self.df.iterrows():
            sig = row['signal']
            close = row['close']
            high = row['high']
            low = row['low']

            # Si une position est ouverte
            if position == 'BUY':
                if low <= trade_sl <= high:
                    position_list.append('CLOSE_BUY_SL')
                    position = None
                elif low <= trade_tp <= high:
                    position_list.append('CLOSE_BUY_TP')
                    position = None
                else:
                    position_list.append('OPEN_BUY')

                trade_id_list.append(trade_counter)
                trade_entry_price_list.append(trade_entry_price)
                trade_tp_list.append(trade_tp)
                trade_sl_list.append(trade_sl)

            elif position == 'SELL':
                if low <= trade_tp <= high:
                    position_list.append('CLOSE_SELL_TP')
                    position = None
                elif low <= trade_sl <= high:
                    position_list.append('CLOSE_SELL_SL')
                    position = None
                else:
                    position_list.append('OPEN_SELL')

                trade_id_list.append(trade_counter)
                trade_entry_price_list.append(trade_entry_price)
                trade_tp_list.append(trade_tp)
                trade_sl_list.append(trade_sl)

            # Si aucune position ouverte, ouvrir selon signal
            elif position is None and sig in ['BUY', 'SELL']:
                trade_counter += 1
                position = sig
                trade_entry_price = row['entry_price']
                trade_tp = row['tp']
                trade_sl = row['sl']

                if sig == 'BUY':
                    position_list.append('OPEN_BUY')
                else:
                    position_list.append('OPEN_SELL')

                trade_id_list.append(trade_counter)
                trade_entry_price_list.append(trade_entry_price)
                trade_tp_list.append(trade_tp)
                trade_sl_list.append(trade_sl)

            # Pas de position ni signal
            else:
                position_list.append(None)
                trade_id_list.append(None)
                trade_entry_price_list.append(None)
                trade_tp_list.append(None)
                trade_sl_list.append(None)

        # Création des colonnes figées
        self.df['position'] = position_list
        self.df['trade_id'] = trade_id_list
        self.df['trade.entry_price'] = trade_entry_price_list
        self.df['trade.tp'] = trade_tp_list
        self.df['trade.sl'] = trade_sl_list

        # Propagation sur toutes les lignes du trade
        for col in ['trade.entry_price', 'trade.tp', 'trade.sl']:
            self.df[col] = self.df.groupby('trade_id')[col].transform(lambda x: x.ffill().bfill())

        return self.df
