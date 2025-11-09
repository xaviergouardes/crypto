import pandas as pd

class OnlyOnePositionTrader:
    def __init__(self, df: pd.DataFrame, tp_pct: float = 1.2, sl_pct: float = 0.6):
        """
        df : DataFrame contenant au moins ['signal','close','high','low']
        tp_pct : Take Profit en pourcentage
        sl_pct : Stop Loss en pourcentage
        """
        self.df = df.copy()
        self.tp_pct = tp_pct / 100
        self.sl_pct = sl_pct / 100

    def run_trades(self):
        position = None
        entry_price = None
        tp_price = None
        sl_price = None
        trade_counter = 0

        position_list = []
        trade_id_list = []
        entry_price_list = []
        tp_list = []
        sl_list = []

        for i, row in self.df.iterrows():
            sig = row['signal']
            close = row['close']
            high = row['high']
            low = row['low']

            # Si une position est ouverte
            if position == 'BUY':
                # Vérifier TP ou SL
                if low <= sl_price <= high:
                    position_list.append('CLOSE_BUY_SL')
                    trade_id_list.append(trade_counter)
                    entry_price_list.append(entry_price)
                    tp_list.append(tp_price)
                    sl_list.append(sl_price)
                    position = None
                elif low <= tp_price <= high:
                    position_list.append('CLOSE_BUY_TP')
                    trade_id_list.append(trade_counter)
                    entry_price_list.append(entry_price)
                    tp_list.append(tp_price)
                    sl_list.append(sl_price)
                    position = None
                else:
                    position_list.append('OPEN_BUY')
                    trade_id_list.append(trade_counter)
                    entry_price_list.append(entry_price)
                    tp_list.append(tp_price)
                    sl_list.append(sl_price)

            elif position == 'SELL':
                if low <= tp_price <= high:
                    position_list.append('CLOSE_SELL_TP')
                    trade_id_list.append(trade_counter)
                    entry_price_list.append(entry_price)
                    tp_list.append(tp_price)
                    sl_list.append(sl_price)
                    position = None
                elif low <= sl_price <= high:
                    position_list.append('CLOSE_SELL_SL')
                    trade_id_list.append(trade_counter)
                    entry_price_list.append(entry_price)
                    tp_list.append(tp_price)
                    sl_list.append(sl_price)
                    position = None
                else:
                    position_list.append('OPEN_SELL')
                    trade_id_list.append(trade_counter)
                    entry_price_list.append(entry_price)
                    tp_list.append(tp_price)
                    sl_list.append(sl_price)

            # Si aucune position ouverte, ouvrir selon signal
            elif position is None and sig in ['BUY', 'SELL']:
                trade_counter += 1
                position = sig
                entry_price = close
                if sig == 'BUY':
                    tp_price = entry_price * (1 + self.tp_pct)
                    sl_price = entry_price * (1 - self.sl_pct)
                    position_list.append('OPEN_BUY')
                else:
                    tp_price = entry_price * (1 - self.tp_pct)
                    sl_price = entry_price * (1 + self.sl_pct)
                    position_list.append('OPEN_SELL')

                trade_id_list.append(trade_counter)
                entry_price_list.append(entry_price)
                tp_list.append(tp_price)
                sl_list.append(sl_price)

            # Sinon pas de position
            else:
                position_list.append(None)
                trade_id_list.append(None)
                entry_price_list.append(None)
                tp_list.append(None)
                sl_list.append(None)

        # Propager entry_price, tp et sl sur toutes les bougies d’un trade
        self.df['position'] = position_list
        self.df['trade_id'] = trade_id_list
        self.df['entry_price'] = entry_price_list
        self.df['tp'] = tp_list
        self.df['sl'] = sl_list

        # Propagation vers le futur pour toutes les bougies entre ouverture et fermeture
        self.df[['entry_price','tp','sl']] = self.df.groupby('trade_id')[['entry_price','tp','sl']].ffill()

        return self.df
