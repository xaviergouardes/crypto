from binance.client import Client
from binance.enums import *
import os

# =========================
# 1️⃣ Configuration Testnet
# =========================
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET, testnet=True)

# =========================
# 2️⃣ Paramètres
# =========================
symbol = "BTCUSDT"
quantity = 0.001

# =========================
# 3️⃣ Lire le carnet d'ordres
# =========================
order_book = client.get_order_book(symbol=symbol, limit=5)
best_ask = float(order_book['asks'][0][0])  # meilleur prix vendeur
best_bid = float(order_book['bids'][0][0])  # meilleur prix acheteur

print(f"📊 Carnet {symbol}")
print(f"Meilleur prix vendeur (ask) : {best_ask}")
print(f"Meilleur prix acheteur (bid): {best_bid}")

# =========================
# 4️⃣ Passer un ordre MARKET (achat)
# =========================
order = client.create_order(
    symbol=symbol,
    side=SIDE_BUY,
    type=ORDER_TYPE_MARKET,
    quantity=quantity
)

# =========================
# 5️⃣ Vérifier le prix exécuté
# =========================
fills = order['fills']
executed_price = sum(float(f['price']) * float(f['qty']) for f in fills) / sum(float(f['qty']) for f in fills)

print(f"\n✅ Ordre exécuté : {order['executedQty']} BTC")
print(f"Prix moyen exécuté : {executed_price} USDT")
print(f"Différence entre prix lu ({best_ask}) et prix exécuté ({executed_price}) : {executed_price - best_ask:.2f} USDT")
