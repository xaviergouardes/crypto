import time
from binance.client import Client
import numpy as np

# ==== CONFIGURATION ====
PAIR = "ETHUSDC"          # Change ici pour basculer de ETHBTC à ETHUSDC etc.
QUANTITY = 0.02
RISK_REWARD = 1.3          # Ratio TP / SL
PRINT_EVERY = 10           # Affichage du prix/support tous les N cycles

# Déduit automatiquement la devise de cotation (quote currency)
QUOTE = PAIR[3:]
BASE = PAIR[:3]

# ==== CLIENT PUBLIC BINANCE ====
client = Client()  # Sans clés API

# ==== VARIABLES GLOBALES ====
open_position = None       # None = pas de trade, sinon "LONG" ou "SHORT"
entry_price = None
stop_loss = None
take_profit = None
cycle_count = 0
pnl_simule = 0.0           # P&L total simulé

# ==== FONCTIONS ====
def get_orderbook(symbol, limit=150):
    """Récupère le carnet d’ordres"""
    depth = client.get_order_book(symbol=symbol, limit=limit)
    bids = [(float(price), float(qty)) for price, qty in depth['bids']]
    asks = [(float(price), float(qty)) for price, qty in depth['asks']]
    return bids, asks

def detect_levels(bids, asks, top_n=15):
    """Détecte les supports et résistances forts : top N volumes"""
    bids_sorted = sorted(bids, key=lambda x: x[1], reverse=True)[:top_n]
    asks_sorted = sorted(asks, key=lambda x: x[1], reverse=True)[:top_n]
    strong_supports = sorted([p for p,q in bids_sorted], reverse=True)
    strong_resistances = sorted([p for p,q in asks_sorted])
    return strong_supports, strong_resistances

def calcul_tp_sl(supports, resistances, position_type, min_gap=1.0):
    """
    Calcule SL et TP selon les règles avec un écart minimum.
    
    LONG : entrée = premier support, SL = deuxième support, TP = première résistance qui > entrée + min_gap
    SHORT : entrée = première résistance, SL = deuxième résistance, TP = premier support qui < entrée - min_gap
    """
    if position_type == "LONG":
        if len(supports) < 2:
            raise ValueError("Pas assez de supports pour calculer SL")
        entry_price = supports[0]
        stop_loss = supports[1]
        # Cherche TP parmi les résistances
        take_profit = None
        for r in resistances:
            if r >= entry_price + min_gap:
                take_profit = r
                break
        if take_profit is None:
            take_profit = entry_price + min_gap  # fallback si aucune résistance ne satisfait la condition

    elif position_type == "SHORT":
        if len(resistances) < 2:
            raise ValueError("Pas assez de résistances pour calculer SL")
        entry_price = resistances[0]
        stop_loss = resistances[1]
        # Cherche TP parmi les supports
        take_profit = None
        for s in supports:
            if s <= entry_price - min_gap:
                take_profit = s
                break
        if take_profit is None:
            take_profit = entry_price - min_gap  # fallback si aucun support ne satisfait la condition

    else:
        raise ValueError("position_type doit être 'LONG' ou 'SHORT'")

    return entry_price, stop_loss, take_profit



def detect_signal(last_price, supports, resistances, spread=0.005):
    """
    Détecte un signal d'entrée (LONG ou SHORT) en fonction du prix et des niveaux.
    spread : marge de déclenchement (ex. 0.001 = 0.1%)
    Retourne (position_type, stop_level) ou (None, None) si aucun signal.
    """
    # ---- SIGNAL ACHAT ----
    if supports and last_price <= supports[0] * (1 + spread):
        return "LONG", supports[0]

    # ---- SIGNAL VENTE ----
    elif resistances and last_price >= resistances[0] * (1 - spread):
        return "SHORT", resistances[0]

    return None, None

def strategy():
    """Stratégie simulée avec P&L"""
    global open_position, entry_price, stop_loss, take_profit, cycle_count, pnl_simule
    cycle_count += 1

    last_price = float(client.get_symbol_ticker(symbol=PAIR)['price'])
    print(f"Prix actuel : {last_price}")

    bids, asks = get_orderbook(PAIR)
    supports, resistances = detect_levels(bids, asks)
    print(f"Supports forts : {supports}")
    print(f"Résistances fortes : {resistances}")



    # Affichage toutes les PRINT_EVERY cycles
    # if cycle_count % PRINT_EVERY == 0:
    #     print(f"\n📊 Cycle {cycle_count}")
    #     print(f"Prix actuel : {last_price}")
    #     print(f"Supports forts : {supports[:10]}")
    #     print(f"Résistances fortes : {resistances[:10]}")
    #     print(f"P&L simulé total : {pnl_simule:.8f} {QUOTE}")

    if open_position is None:
        position_type, stop_level = detect_signal(last_price, supports, resistances)
        if position_type:
            open_position = position_type
            entry_price = last_price
            # stop_loss, take_profit = calcul_tp_sl(entry_price, stop_level, position_type)
            entry_price, stop_loss, take_profit = calcul_tp_sl(supports, resistances, position_type)
            if position_type == "LONG":
                print(f"🟢 Signal Achat @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f} | stop_level = {stop_level}")
            else:
                print(f"🔴 Signal Vente @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f} | stop_level = {stop_level}")


    else:
        # Calcul P&L en temps réel
        # pnl_actuel = (last_price - entry_price) * QUANTITY if open_position == "LONG" else (entry_price - last_price) * QUANTITY
        if open_position == "LONG":
            pnl_actuel = (last_price - entry_price) * QUANTITY  # ETH * (USDC/ETH) = USDC
        elif open_position == "SHORT":
            pnl_actuel = (entry_price - last_price) * QUANTITY

        # if cycle_count % PRINT_EVERY == 0:
        #     print(f"📌 Position simulée : {open_position} @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f} | "
        #           f"P&L actuel = {pnl_actuel:.8f} {QUOTE} ou {BASE} | Prix actuel = {last_price:.8f}")

        # ---- GESTION DE SORTIE SIMULÉE ----
        if open_position == "LONG":
            if last_price <= stop_loss:
                pnl_simule += pnl_actuel
                print(f"❌ Stop Loss touché ({last_price:.8f}) -> fermeture LONG | P&L = {pnl_actuel:.8f} {QUOTE}")
                open_position = None
            elif last_price >= take_profit:
                pnl_simule += pnl_actuel
                print(f"✅ Take Profit atteint ({last_price:.8f}) -> fermeture LONG | P&L = {pnl_actuel:.8f} {QUOTE}")
                open_position = None
        elif open_position == "SHORT":
            if last_price >= stop_loss:
                pnl_simule += pnl_actuel
                print(f"❌ Stop Loss touché ({last_price:.8f}) -> fermeture SHORT | P&L = {pnl_actuel:.8f} {QUOTE}")
                open_position = None
            elif last_price <= take_profit:
                pnl_simule += pnl_actuel
                print(f"✅ Take Profit atteint ({last_price:.8f}) -> fermeture SHORT | P&L = {pnl_actuel:.8f} {QUOTE}")
                open_position = None

# ==== BOUCLE PRINCIPALE ====
if __name__ == "__main__":
    try:
        while True:
            strategy()
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nArrêt manuel de la simulation.")
        print(f"P&L simulé final : {pnl_simule:.8f} {QUOTE}")
