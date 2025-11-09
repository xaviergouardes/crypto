import pandas as pd

# === CONFIGURATION ===
path_file = "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250901_20251104.csv"
capital_initial = 1000.0
sl_pct = 0.05   # Stop Loss à -1%

# === CHARGEMENT DES DONNÉES ===
df = pd.read_csv(path_file, parse_dates=['timestamp'])
df.set_index('timestamp', inplace=True)

# === INDICATEURS ===
df['sma200'] = df['close'].rolling(window=200).mean()
tolerance = df['close'].mean() * 0.001

# === GÉNÉRATION DES SIGNAUX ===
df['signal'] = 0
df.loc[(df['close'].shift(1) + tolerance < df['sma200'].shift(1)) &
       (df['close'] - tolerance > df['sma200']), 'signal'] = 1
df.loc[(df['close'].shift(1) - tolerance > df['sma200'].shift(1)) &
       (df['close'] + tolerance < df['sma200']), 'signal'] = -1

# === INITIALISATION DU PORTFOLIO ===
df['position'] = 0
df['usdc'] = capital_initial
df['etc'] = 0.0
df['trade_pnl'] = 0.0
df['equity'] = capital_initial
df['action'] = ""
df['trade_number'] = 0
df['win'] = 0
df['win_rate'] = 0.0

usdc = capital_initial
position = 0
entry_price = None
sl_price = None
trade_count = 0
wins = 0
usdc_invested = 0.0

# === SIMULATION DE TRADING ===
for i in range(len(df)):
    price = df.iloc[i]['close']
    signal = df.iloc[i]['signal']
    action = ""
    pnl = 0

    # --- Stop Loss ---
    if position == 1 and entry_price is not None and price <= sl_price:
        pnl = usdc_invested * (price - entry_price) / entry_price
        usdc += usdc_invested + pnl
        position = 0
        entry_price = None
        sl_price = None
        action = "VENTE_SL"

    # --- Entrée en position ---
    if signal == 1 and position == 0:
        usdc_invested = usdc
        entry_price = price
        sl_price = entry_price * (1 - sl_pct)
        position = 1
        usdc = 0
        action = "ACHAT"

    # --- Sortie normale via signal ---
    if signal == -1 and position == 1 and entry_price is not None and action == "":
        pnl = usdc_invested * (price - entry_price) / entry_price
        usdc += usdc_invested + pnl
        position = 0
        entry_price = None
        sl_price = None
        action = "VENTE_SIGNAL"

    # --- Mise à jour du DataFrame ---
    if position == 1 and entry_price is not None:
        equity = usdc + usdc_invested * (price / entry_price)
        etc_amount = usdc_invested / entry_price
    else:
        equity = usdc
        etc_amount = 0

    df.iloc[i, df.columns.get_loc('position')] = position
    df.iloc[i, df.columns.get_loc('usdc')] = usdc
    df.iloc[i, df.columns.get_loc('etc')] = etc_amount
    df.iloc[i, df.columns.get_loc('trade_pnl')] = pnl
    df.iloc[i, df.columns.get_loc('equity')] = equity
    df.iloc[i, df.columns.get_loc('action')] = action

    # --- Statistiques ---
    if action in ["VENTE_SIGNAL", "VENTE_SL"]:
        trade_count += 1
        df.iloc[i, df.columns.get_loc('trade_number')] = trade_count
        if pnl > 0:
            wins += 1
            df.iloc[i, df.columns.get_loc('win')] = 1
        df.iloc[i, df.columns.get_loc('win_rate')] = wins / trade_count * 100

# === FILTRAGE DES TRADES EFFECTIFS ===
df_trades = df[df['action'] != ""][['close', 'sma200', 'action', 'trade_pnl', 'equity', 'trade_number', 'win', 'win_rate']]

# === RÉSULTATS ===
print("\n=== JOURNAL DES TRADES ===")
print(df_trades)

print("\nÉquity finale :", round(df['equity'].iloc[-1], 2), "USDC")
print("Nombre de trades :", trade_count)
print("Win rate final :", round(wins / trade_count * 100, 2), "%")
