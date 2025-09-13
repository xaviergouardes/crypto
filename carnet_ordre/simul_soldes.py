from datetime import datetime

# Tes trades réels (liste partielle, à compléter avec tous tes trades)
# Format : (datetime, pair, side, qty_base, quote_qty, commission, commission_asset)
trades = [
    ("2025-09-11 21:07:44.037000", "BTCUSDC", "Achat", 0.00087, 99.6214902, 0.0000, "BTC"),
    ("2025-09-11 21:07:44.264000", "ACHBTC", "Achat", 4833.0, 0.00086994, 0.0, "ACH"),
    ("2025-09-11 21:07:44.490000", "ACHUSDC", "Vente", 5117.0, 101.87947, 0.0, "ACH"),
    ("2025-09-11 21:07:46.452000", "BTCUSDC", "Achat", 0.00087, 99.6214902, 0.0, "BTC"),
    ("2025-09-11 21:07:46.679000", "ACHBTC", "Achat", 4833.0, 0.00086994, 0.0, "ACH"),
    ("2025-09-11 21:07:46.904000", "ACHUSDC", "Vente", 5117.0, 101.87947, 0.0, "ACH"),
]

# Solde initial
saldo = {
    "ACH": 0.0,
    "BTC": 0.0,
    "USDC": 0.0
}

# Fonction pour appliquer un trade avec frais exacts
def apply_trade(trade, saldo):
    dt, pair, side, qty_base, quote_qty, commission, commission_asset = trade
    base, quote = pair[:3], pair[3:]

    if side == "Achat":
        # Achat : tu reçois le base, dépenses le quote
        saldo[base] += qty_base
        saldo[quote] -= quote_qty
        # Frais
        if commission_asset == base:
            saldo[base] -= commission
        elif commission_asset == quote:
            saldo[quote] -= commission
    elif side == "Vente":
        # Vente : tu dépenses le base, reçois le quote
        saldo[base] -= qty_base
        saldo[quote] += quote_qty
        # Frais
        if commission_asset == base:
            saldo[base] -= commission
        elif commission_asset == quote:
            saldo[quote] -= commission

    return saldo

# Tri par date
trades_sorted = sorted(trades, key=lambda x: x[0])

# Application et affichage
for t in trades_sorted:
    saldo = apply_trade(t, saldo)
    dt, pair, side, qty_base, quote_qty, commission, commission_asset = t
    print(f"{dt} | {pair} | {side} | Solde après trade: ACH={saldo['ACH']:.2f}, BTC={saldo['BTC']:.6f}, USDC={saldo['USDC']:.2f}")

