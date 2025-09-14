import os
import random
import time
from binance.client import Client
from decimal import Decimal, ROUND_DOWN

# 🔑 Clés API depuis variables d'environnement
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    raise Exception("Clés API manquantes !")

client = Client(API_KEY, API_SECRET, testnet=True)

symbol = "BTCUSDT"
quantity_range = (0.001, 0.002)  # quantités simulées
delay = 3                        # secondes entre chaque ordre

# 🔹 Récupération des filtres LOT_SIZE pour tronquer la quantité
symbol_info = client.get_symbol_info(symbol)
lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
min_qty = float(lot_size_filter['minQty'])
step_size = float(lot_size_filter['stepSize'])

def round_step(value, step):
    """Arrondir la quantité au step correct pour Binance"""
    step_dec = Decimal(str(step))
    value_dec = Decimal(str(value))
    rounded = (value_dec // step_dec) * step_dec
    return float(rounded)

print("🚀 Bot simulateur de marché Testnet avec ordres MARKET")

try:
    while True:
        # 🔹 Choisir aléatoirement achat ou vente
        side = random.choice(["BUY", "SELL"])
        qty = round_step(random.uniform(*quantity_range), step_size)
        if qty < min_qty:
            qty = min_qty

        # 🔹 Passer l'ordre MARKET
        if side == "BUY":
            order = client.order_market_buy(symbol=symbol, quantity=qty)
        else:
            order = client.order_market_sell(symbol=symbol, quantity=qty)

        # 🔹 Récupérer le prix d'exécution réel
        executed_qty = sum([float(f['qty']) for f in order['fills']])
        executed_price = sum([float(f['price']) * float(f['qty']) for f in order['fills']]) / executed_qty

        print(f"✅ {side} exécuté : {executed_qty} BTC à {round(executed_price,2)} USDT | OrderID: {order['orderId']}")

        time.sleep(delay)

except KeyboardInterrupt:
    print("\n🛑 Simulation de marché Testnet arrêtée proprement.")
