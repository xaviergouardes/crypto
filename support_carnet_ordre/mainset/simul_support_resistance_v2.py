import requests
import numpy as np
import time
import os

BINANCE_API_URL = "https://api.binance.com/api/v3/depth"

def detect_zones(levels, volumes, seuil_volume=0.05, seuil_distance=0.001):
    """Détection de zones de support/résistance à partir du carnet d'ordres"""
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


def get_orderbook(symbol="ETHUSDC", limit=100):
    """Récupère le carnet d'ordres depuis l'API de Binance"""
    url = f"{BINANCE_API_URL}?symbol={symbol}&limit={limit}"
    response = requests.get(url)
    data = response.json()

    bids = [(float(price), float(qty)) for price, qty in data['bids']]
    asks = [(float(price), float(qty)) for price, qty in data['asks']]

    return bids, asks


if __name__ == "__main__":
    REFRESH_INTERVAL = 5  # secondes entre chaque mise à jour

    while True:
        try:
            # 1. Récupération du carnet d'ordres
            bids, asks = get_orderbook("ETHUSDC", limit=500)

            # 2. Séparation prix/volumes
            bid_prices, bid_volumes = zip(*bids)
            ask_prices, ask_volumes = zip(*asks)

            # 3. Détection des zones
            support_zones = detect_zones(bid_prices, bid_volumes)
            resistance_zones = detect_zones(ask_prices, ask_volumes)

            # 4. Effacer l’écran pour une vue "live"
            os.system('cls' if os.name == 'nt' else 'clear')

            # 5. Affichage des résultats
            print("=== Binance ETH/USDC - Support & Résistance ===\n")
            print(">>> SUPPORTS (Bids) :")
            for z in support_zones[:5]:
                print(f"Prix moyen: {z[0]:.2f}, Volume total: {z[1]:.2f}")

            print("\n>>> RÉSISTANCES (Asks) :")
            for z in resistance_zones[:5]:
                print(f"Prix moyen: {z[0]:.2f}, Volume total: {z[1]:.2f}")

            # 6. Pause avant rafraîchissement
            time.sleep(REFRESH_INTERVAL)

        except KeyboardInterrupt:
            print("\nArrêt manuel par l'utilisateur.")
            break
        except Exception as e:
            print(f"Erreur: {e}")
            time.sleep(REFRESH_INTERVAL)
