from binance.client import Client
from binance.exceptions import BinanceAPIException
import time
import os

# ⚙️ Connexion au spot testnet
client = Client(None, None, testnet=True)

# 🔄 Triplette pour arbitrage triangulaire
PAIR1 = "ETHUSDT"  # Achat ETH avec USDT
PAIR2 = "ETHBTC"   # Vendre ETH contre BTC
PAIR3 = "BTCUSDT"  # Vendre BTC contre USDT

# Montant de départ en USDT
initial_amount = 100

def get_price(symbol):
    """Récupère le dernier prix pour une paire donnée"""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except BinanceAPIException as e:
        print(f"Erreur API sur {symbol}: {e}")
        return None

while True:
    try:
        # 📊 Récupération des prix
        price1 = get_price(PAIR1)  # ETH/USDT
        price2 = get_price(PAIR2)  # ETH/BTC
        price3 = get_price(PAIR3)  # BTC/USDT

        if None in (price1, price2, price3):
            continue

        # 🔄 Simulation de l’arbitrage
        usdt = initial_amount
        eth = usdt / price1          # USDT → ETH
        btc = eth * price2           # ETH → BTC
        final_usdt = btc * price3    # BTC → USDT

        profit = final_usdt - initial_amount

        print(f"\n💹 Arbitrage Test:")
        print(f"  Start: {initial_amount} USDT")
        print(f"  End:   {final_usdt:.2f} USDT")
        print(f"  Profit: {profit:.2f} USDT")

        if profit > 0:
            print("✅ Opportunité détectée !")
            # Ici tu pourrais placer les ordres réels :
            # client.order_market_buy(symbol=PAIR1, quantity=...)
            # ...

        time.sleep(5)

    except Exception as e:
        print(f"Erreur: {e}")
        time.sleep(5)
