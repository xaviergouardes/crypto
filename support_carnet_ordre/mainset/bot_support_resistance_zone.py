import time
from binance.client import Client
import numpy as np

# ==== CONFIGURATION ====
PAIR = "ETHUSDC"          # Change ici pour basculer de ETHBTC à ETHUSDC etc.
QUANTITY = 0.05
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
solde = 100.0

# ==== NOUVELLE FONCTION : regroupement de zones ====
def detect_zones(levels, volumes, seuil_volume=0.05, seuil_distance=0.001):
    """Regroupe les niveaux proches et filtre les petits volumes"""
    if not levels:
        return []

    max_vol = max(volumes)
    filtres = [(p, v) for p, v in zip(levels, volumes) if v > seuil_volume * max_vol]
    filtres.sort(key=lambda x: x[0])  

    zones = []
    if not filtres:
        return zones

    zone_actuelle = [[filtres[0][0]], [filtres[0][1]]]

    for prix, vol in filtres[1:]:
        prix_moyen_zone = np.mean(zone_actuelle[0])
        if abs(prix - prix_moyen_zone) / prix_moyen_zone < seuil_distance:
            zone_actuelle[0].append(prix)
            zone_actuelle[1].append(vol)
        else:
            zones.append((np.mean(zone_actuelle[0]), sum(zone_actuelle[1])))
            zone_actuelle = [[prix], [vol]]

    zones.append((np.mean(zone_actuelle[0]), sum(zone_actuelle[1])))

    zones.sort(key=lambda x: x[1], reverse=True)
    return zones


def get_orderbook(symbol, limit=500):
    """Récupère le carnet d’ordres"""
    depth = client.get_order_book(symbol=symbol, limit=limit)
    bids = [(float(price), float(qty)) for price, qty in depth['bids']]
    asks = [(float(price), float(qty)) for price, qty in depth['asks']]
    return bids, asks


def detect_levels(bids, asks, top_n=5):
    """
    Détecte les supports/résistances via regroupement en zones.
    Retourne deux listes de floats : supports et résistances.
    """
    # Séparer les prix et volumes
    bid_prices, bid_volumes = zip(*bids)
    ask_prices, ask_volumes = zip(*asks)

    # Détection des zones consolidées
    support_zones = detect_zones(bid_prices, bid_volumes)
    resistance_zones = detect_zones(ask_prices, ask_volumes)

    # Conversion np.float64 -> float et garder top_n zones
    strong_supports = [float(p) for p, v in support_zones[:top_n]]
    strong_resistances = [float(p) for p, v in resistance_zones[:top_n]]

    # Tri des supports (du plus proche du prix actuel au plus bas)
    strong_supports.sort(reverse=True)
    # Tri des résistances (du plus proche du prix actuel au plus haut)
    strong_resistances.sort()

    return strong_supports, strong_resistances



def calcul_tp_sl(supports, resistances, position_type, min_gap=1.0):
    """Calcule SL et TP selon les zones détectées"""
    if position_type == "LONG":
        if len(supports) < 2:
            raise ValueError("Pas assez de supports pour calculer SL")
        entry_price = supports[1]
        stop_loss = supports[2]
        take_profit = resistances[2]
        # take_profit = None
        # for r in resistances:
        #     if r >= entry_price + min_gap:
        #         take_profit = r
        #         break
        # if take_profit is None:
        #     take_profit = entry_price + min_gap  

    elif position_type == "SHORT":
        if len(resistances) < 2:
            raise ValueError("Pas assez de résistances pour calculer SL")
        entry_price = resistances[1]
        stop_loss = resistances[2]
        take_profit = supports[2]
        # take_profit = None
        # for s in supports:
        #     if s <= entry_price - min_gap:
        #         take_profit = s
        #         break
        # if take_profit is None:
        #     take_profit = entry_price - min_gap  

    else:
        raise ValueError("position_type doit être 'LONG' ou 'SHORT'")

    return entry_price, stop_loss, take_profit


def detect_signal(last_price, supports, resistances, spread=0.005):
    """Détecte un signal LONG/SHORT en fonction des zones"""
    if supports and last_price <= supports[0] * (1 + spread):
        return "LONG", supports[0]
    elif resistances and last_price >= resistances[0] * (1 - spread):
        return "SHORT", resistances[0]
    return None, None


def strategy():
    """Stratégie simulée avec P&L"""
    global open_position, entry_price, stop_loss, take_profit, cycle_count, pnl_simule, solde
    cycle_count += 1

    last_price = float(client.get_symbol_ticker(symbol=PAIR)['price'])
    # print(f"Prix actuel : {last_price}")

    bids, asks = get_orderbook(PAIR)
    supports, resistances = detect_levels(bids, asks)

    # print(f"Supports (zones) : {supports}")
    # print(f"Résistances (zones) : {resistances}")

    if open_position is None:
        position_type, stop_level = detect_signal(last_price, supports, resistances)
        if position_type:
            open_position = position_type
            entry_price = last_price
            entry_price, stop_loss, take_profit = calcul_tp_sl(supports, resistances, position_type)
            if position_type == "LONG":
                print(f"🟢 Signal Achat @ {entry_price:.2f} | SL = {stop_loss:.2f} | TP = {take_profit:.2f}")
            else:
                print(f"🔴 Signal Vente @ {entry_price:.2f} | SL = {stop_loss:.2f} | TP = {take_profit:.2f}")

    else:
        if open_position == "LONG":
            pnl_actuel = (last_price - entry_price) * QUANTITY  
        elif open_position == "SHORT":
            pnl_actuel = (entry_price - last_price) * QUANTITY

        if open_position == "LONG":
            if last_price <= stop_loss:
                pnl_simule = - (entry_price - stop_loss) * QUANTITY  
                solde += pnl_simule
                open_position = None
                print(f"❌ Stop Loss LONG ({stop_loss:.2f}) | P&L = {pnl_simule:.4f} {QUOTE} | Solde = {solde:.2f} {QUOTE}")
            elif last_price >= take_profit:
                pnl_simule = (take_profit - entry_price) * QUANTITY  
                solde += pnl_simule
                open_position = None
                print(f"✅ Take Profit LONG ({take_profit:.2f}) | P&L = {pnl_simule:.4f} {QUOTE} | Solde = {solde:.2f} {QUOTE}")
        elif open_position == "SHORT":
            if last_price >= stop_loss:
                pnl_simule = - (entry_price - stop_loss) * QUANTITY  
                solde += pnl_simule
                open_position = None
                print(f"❌ Stop Loss SHORT ({stop_loss:.2f}) | P&L = {pnl_simule:.4f} {QUOTE} | Solde = {solde:.2f} {QUOTE}")
            elif last_price <= take_profit:
                pnl_simule = (take_profit - entry_price) * QUANTITY   
                solde += pnl_simule
                open_position = None
                print(f"✅ Take Profit SHORT ({take_profit:.2f}) | P&L = {pnl_simule:.4f} {QUOTE} | Solde = {solde:.2f} {QUOTE}")


# ==== BOUCLE PRINCIPALE ====
if __name__ == "__main__":
    try:
        while True:
            strategy()
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nArrêt manuel de la simulation.")
        print(f"P&L simulé final : {pnl_simule:.2f} {QUOTE}")
