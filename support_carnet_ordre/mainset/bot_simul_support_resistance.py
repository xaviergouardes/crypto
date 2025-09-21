import time
from binance.client import Client
import numpy as np

# ==== CONFIGURATION ====
SYMBOL = "ETHBTC"
QUANTITY = 0.01
RISK_REWARD = 1.5          # Ratio TP / SL
PRINT_EVERY = 50           # Affichage du prix/support tous les N cycles

# ==== CLIENT PUBLIC BINANCE ====
# Seule la lecture publique est nécessaire
client = Client()  # Sans clés API

# ==== VARIABLES GLOBALES ====
open_position = None       # None = pas de trade, sinon "LONG" ou "SHORT"
entry_price = None
stop_loss = None
take_profit = None
cycle_count = 0
pnl_simule = 0.0           # P&L total simulé

# ==== FONCTIONS ====
def get_orderbook(symbol, limit=100):
    """Récupère le carnet d’ordres"""
    depth = client.get_order_book(symbol=symbol, limit=limit)
    bids = [(float(price), float(qty)) for price, qty in depth['bids']]
    asks = [(float(price), float(qty)) for price, qty in depth['asks']]
    return bids, asks

def detect_levels(bids, asks, top_n=10):
    """Détecte les supports et résistances forts : top N volumes"""
    bids_sorted = sorted(bids, key=lambda x: x[1], reverse=True)[:top_n]
    asks_sorted = sorted(asks, key=lambda x: x[1], reverse=True)[:top_n]
    strong_supports = sorted([p for p,q in bids_sorted], reverse=True)
    strong_resistances = sorted([p for p,q in asks_sorted])
    return strong_supports, strong_resistances

def strategy():
    """Stratégie simulée avec P&L"""
    global open_position, entry_price, stop_loss, take_profit, cycle_count, pnl_simule

    bids, asks = get_orderbook(SYMBOL)
    supports, resistances = detect_levels(bids, asks)
    last_price = float(client.get_symbol_ticker(symbol=SYMBOL)['price'])
    cycle_count += 1

    # Affichage toutes les PRINT_EVERY cycles
    if cycle_count % PRINT_EVERY == 0:
        print(f"\n📊 Cycle {cycle_count}")
        print(f"Prix actuel : {last_price}")
        print(f"Supports forts : {supports[:10]}")
        print(f"Résistances fortes : {resistances[:10]}")
        print(f"P&L simulé total : {pnl_simule:.8f} BTC")

    if open_position is None:
        # ---- SIGNAL SIMULATION ACHAT ----
        if supports and last_price <= supports[0] * 1.001:
            open_position = "LONG"
            entry_price = last_price
            stop_loss = supports[0] * 0.999
            take_profit = entry_price + (entry_price - stop_loss) * RISK_REWARD
            print(f"🟢 Signal Achat @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f}")

        # ---- SIGNAL SIMULATION VENTE ----
        elif resistances and last_price >= resistances[0] * 0.999:
            open_position = "SHORT"
            entry_price = last_price
            stop_loss = resistances[0] * 1.001
            take_profit = entry_price - (stop_loss - entry_price) * RISK_REWARD
            print(f"🔴 Signal Vente @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f}")

    else:
        # Calcul P&L en temps réel
        pnl_actuel = (last_price - entry_price) * QUANTITY if open_position == "LONG" else (entry_price - last_price) * QUANTITY
        print(f"📌 Position simulée : {open_position} @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f} | P&L actuel = {pnl_actuel:.8f} BTC")

        # ---- GESTION DE SORTIE SIMULÉE ----
        if open_position == "LONG":
            if last_price <= stop_loss:
                pnl_simule += pnl_actuel
                print(f"❌ Stop Loss touché ({last_price:.8f}) -> fermeture LONG | P&L = {pnl_actuel:.8f} BTC")
                open_position = None
            elif last_price >= take_profit:
                pnl_simule += pnl_actuel
                print(f"✅ Take Profit atteint ({last_price:.8f}) -> fermeture LONG | P&L = {pnl_actuel:.8f} BTC")
                open_position = None
        elif open_position == "SHORT":
            if last_price >= stop_loss:
                pnl_simule += pnl_actuel
                print(f"❌ Stop Loss touché ({last_price:.8f}) -> fermeture SHORT | P&L = {pnl_actuel:.8f} BTC")
                open_position = None
            elif last_price <= take_profit:
                pnl_simule += pnl_actuel
                print(f"✅ Take Profit atteint ({last_price:.8f}) -> fermeture SHORT | P&L = {pnl_actuel:.8f} BTC")
                open_position = None

# ==== BOUCLE PRINCIPALE ====
if __name__ == "__main__":
    try:
        while True:
            strategy()
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nArrêt manuel de la simulation.")
        print(f"P&L simulé final : {pnl_simule:.8f} BTC")
