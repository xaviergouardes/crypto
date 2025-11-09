import pandas as pd

pd.set_option('display.max_rows', None)

# === CONFIGURATION ===
path_file = "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250901_20251104.csv"
usdc_initial = 1000.0
tp_pct = 0.012  # Take Profit 2%
sl_pct = 0.007  # Stop Loss 1%

# === Chargement des données ===
df = pd.read_csv(path_file, parse_dates=['timestamp'])
df.set_index('timestamp', inplace=True)

# === Calcul SMA200 ===
df['sma200'] = df['close'].rolling(window=200).mean()

# === Génération signaux simples SMA cross ===
df['signal'] = 0
df.loc[(df['close'].shift(1) < df['sma200'].shift(1)) & (df['close'] > df['sma200']), 'signal'] = 1  # ACHAT
df.loc[(df['close'].shift(1) > df['sma200'].shift(1)) & (df['close'] < df['sma200']), 'signal'] = -1 # VENTE

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

for ts, row in df.iterrows():
    price = row['close']
    high = row['high']
    low = row['low']
    sig = row['signal']

    # Vérification si position ouverte
    if position is None:
        # Ouvrir position si signal
        if sig == 1:  # LONG
            position = 'LONG'
            entry_price = price
            usdc_invested = equity
            sl_price = entry_price * (1 - sl_pct)
            tp_price = entry_price * (1 + tp_pct)
            trades.append({'timestamp': ts, 'close': price, 'sma200': row['sma200'],
                           'action': 'ACHAT', 'trade_pnl': 0.0, 'equity': equity,
                           'trade_number': trade_number, 'win': 0, 'win_rate': 0.0})
        elif sig == -1:  # SHORT
            position = 'SHORT'
            entry_price = price
            usdc_invested = equity
            sl_price = entry_price * (1 + sl_pct)
            tp_price = entry_price * (1 - tp_pct)
            trades.append({'timestamp': ts, 'close': price, 'sma200': row['sma200'],
                           'action': 'VENTE', 'trade_pnl': 0.0, 'equity': equity,
                           'trade_number': trade_number, 'win': 0, 'win_rate': 0.0})

    else:
        # Vérifier si SL ou TP touché dans cette bougie
        close_trade = False
        trade_pnl = 0.0
        win = 0
        action_type = ''
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

            trades.append({'timestamp': ts, 'close': close_price, 'sma200': row['sma200'],
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
pd.set_option('display.max_rows', None)
print("=== JOURNAL DES TRADES ===")
print(df_trades)

print(f"\nÉquity finale : {equity:.2f} USDC")
print(f"Nombre de trades : {trade_number}")
print(f"Win rate final : {win_rate:.2f} %")
