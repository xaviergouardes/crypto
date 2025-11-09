import pandas as pd

pd.set_option('display.max_rows', None)

# === CONFIGURATION ===
path_file = "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250901_20251104.csv"
usdc_initial = 1000.0
tp_pct = 0.012  # Take Profit 1.2%
sl_pct = 0.006   # Stop Loss 1%
ema_length = 25
min_candle_pct = 0.003  # 0.2% de corps pour être considérée "grande"

# === Chargement des données ===
df = pd.read_csv(path_file, parse_dates=['timestamp'])
df.set_index('timestamp', inplace=True)

# === Calcul EMA200 ===
df['ema200'] = df['close'].ewm(span=ema_length, adjust=False).mean()

# === Calcul taille du corps de la bougie ===
df['body'] = abs(df['close'] - df['open'])
df['body_pct'] = df['body'] / df['open']

# === Journal des trades ===
trades = []
equity = usdc_initial
position = None
entry_price = None
usdc_invested = None
sl_price = None
tp_price = None
trade_number = 0
wins = 0
win_rate = 0.0

for i in range(1, len(df)):
    prev = df.iloc[i-1]
    curr = df.iloc[i]
    price = curr['close']
    high = curr['high']
    low = curr['low']
    candle_size = curr['body_pct']

    # === Génération des signaux ===
    signal = 0
    # LONG : EMA crossed up by body & grande bougie haussière
    if (prev['close'] < prev['ema200'] and curr['close'] > curr['ema200'] 
        and curr['close'] > curr['open'] and candle_size >= min_candle_pct):
        signal = 1
    # SHORT : EMA crossed down by body & grande bougie baissière
    elif (prev['close'] > prev['ema200'] and curr['close'] < curr['ema200'] 
          and curr['close'] < curr['open'] and candle_size >= min_candle_pct):
        signal = -1

    # === Gestion position ===
    if position is None:
        if signal == 1:  # LONG
            position = 'LONG'
            entry_price = price
            usdc_invested = equity
            sl_price = entry_price * (1 - sl_pct)
            tp_price = entry_price * (1 + tp_pct)
            trades.append({'timestamp': curr.name, 'close': price, 'ema200': curr['ema200'],
                           'action': 'ACHAT', 'trade_pnl': 0.0, 'equity': equity,
                           'trade_number': trade_number, 'win': 0, 'win_rate': win_rate})
        elif signal == -1:  # SHORT
            position = 'SHORT'
            entry_price = price
            usdc_invested = equity
            sl_price = entry_price * (1 + sl_pct)
            tp_price = entry_price * (1 - tp_pct)
            trades.append({'timestamp': curr.name, 'close': price, 'ema200': curr['ema200'],
                           'action': 'VENTE', 'trade_pnl': 0.0, 'equity': equity,
                           'trade_number': trade_number, 'win': 0, 'win_rate': win_rate})
    else:
        # Vérifier si SL ou TP touché
        close_trade = False
        trade_pnl = 0.0
        action_type = ''
        win = 0

        if position == 'LONG':
            if low <= sl_price:
                close_price = sl_price
                trade_pnl = (close_price - entry_price) / entry_price * usdc_invested
                close_trade = True
                action_type = 'SL_LONG'
            elif high >= tp_price:
                close_price = tp_price
                trade_pnl = (close_price - entry_price) / entry_price * usdc_invested
                close_trade = True
                action_type = 'TP_LONG'
        elif position == 'SHORT':
            if high >= sl_price:
                close_price = sl_price
                trade_pnl = (entry_price - close_price) / entry_price * usdc_invested
                close_trade = True
                action_type = 'SL_SHORT'
            elif low <= tp_price:
                close_price = tp_price
                trade_pnl = (entry_price - close_price) / entry_price * usdc_invested
                close_trade = True
                action_type = 'TP_SHORT'

        if close_trade:
            equity += trade_pnl
            trade_number += 1
            win = 1 if trade_pnl > 0 else 0
            wins += win
            win_rate = wins / trade_number * 100

            trades.append({'timestamp': curr.name, 'close': close_price, 'ema200': curr['ema200'],
                           'action': action_type, 'trade_pnl': trade_pnl,
                           'equity': equity, 'trade_number': trade_number, 'win': win, 'win_rate': win_rate})

            # Reset position
            position = None
            entry_price = None
            usdc_invested = None
            sl_price = None
            tp_price = None



# === Affichage du journal des trades ===
df_trades = pd.DataFrame(trades)
print("=== JOURNAL DES TRADES ===")
print(df_trades)

print(f"\nÉquity finale : {equity:.2f} USDC")
print(f"Nombre de trades : {trade_number}")
print(f"Win rate final : {win_rate:.2f} %")
