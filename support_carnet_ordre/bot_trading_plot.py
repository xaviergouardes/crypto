import time
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import numpy as np
import os

# ==== CONFIGURATION ====
SYMBOL = "ETHBTC"
QUANTITY = 0.01
RISK_REWARD = 1.5          # Ratio TP / SL
PRINT_EVERY = 10           # Affichage du prix/support tous les N cycles

# ==== LECTURE DES CLÉS TESTNET ====
BINANCE_TESTNET_API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
BINANCE_TESTNET_API_SECRET = os.getenv("BINANCE_TESTNET_API_SECRET")

if not BINANCE_TESTNET_API_KEY or not BINANCE_TESTNET_API_SECRET:
    raise ValueError("Clés Testnet Binance non définies dans les variables d'environnement !")

# ==== CONNEXION TESTNET SPOT ====
client = Client(BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_API_SECRET)
client.API_URL = 'https://testnet.binance.vision/api'

# ==== VARIABLES GLOBALES ====
open_position = None       # None = pas de trade, sinon "LONG" ou "SHORT"
entry_price = None
stop_loss = None
take_profit = None
cycle_count = 0

# ==== FONCTIONS ====
def round_price(symbol, price):
    """Arrondit le prix selon le tick size de la paire"""
    info = client.get_symbol_info(symbol)
    for f in info['filters']:
        if f['filterType'] == 'PRICE_FILTER':
            tick_size = float(f['tickSize'])
            return round(price / tick_size) * tick_size
    return price

def afficher_soldes():
    """Affiche les soldes ETH et BTC disponibles sur le compte"""
    try:
        account = client.get_account()
        balances = {b['asset']: float(b['free']) for b in account['balances'] if b['asset'] in ["ETH","BTC"]}
        print("\n💰 Soldes disponibles :")
        for asset, amount in balances.items():
            print(f" - {asset} : {amount:.8f}")
    except BinanceAPIException as e:
        print("Erreur lors de la récupération des soldes :", e)

def get_orderbook(symbol, limit=100):
    """Récupère le carnet d’ordres"""
    depth = client.get_order_book(symbol=symbol, limit=limit)
    bids = [(float(price), float(qty)) for price, qty in depth['bids']]
    asks = [(float(price), float(qty)) for price, qty in depth['asks']]
    return bids, asks

def detect_levels(bids, asks, top_n=10):
    """
    Détecte les supports et résistances forts à partir du carnet.
    - bids : liste de tuples (prix, quantité) côté achat
    - asks : liste de tuples (prix, quantité) côté vente
    - top_n : nombre de niveaux les plus importants à retourner
    """
    # Crée des dictionnaires prix → volume
    buy_volumes = {}
    sell_volumes = {}

    for price, qty in bids:
        buy_volumes[price] = buy_volumes.get(price, 0) + qty
    for price, qty in asks:
        sell_volumes[price] = sell_volumes.get(price, 0) + qty

    # Trie par volume décroissant et prend les top_n
    top_buys = sorted(buy_volumes.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_sells = sorted(sell_volumes.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # On ne garde que les prix
    strong_supports = sorted([p for p, v in top_buys], reverse=True)  # du plus haut au plus bas
    strong_resistances = sorted([p for p, v in top_sells])             # du plus bas au plus haut

    return strong_supports, strong_resistances

def place_simple_orders(symbol, side, quantity, sl, tp):
    """
    Remplace l'OCO par 2 ordres simples
    """
    try:
        # STOP LIMIT
        stop_limit_side = SIDE_SELL if side == SIDE_BUY else SIDE_BUY
        client.create_order(
            symbol=symbol,
            side=stop_limit_side,
            type=ORDER_TYPE_STOP_LOSS_LIMIT,
            quantity=quantity,
            price=f"{sl:.8f}",
            stopPrice=f"{sl:.8f}",
            timeInForce=TIME_IN_FORCE_GTC
        )
        print(f"✅ Stop-Limit placé @ {sl:.8f}")

        # LIMIT TP
        limit_side = SIDE_SELL if side == SIDE_BUY else SIDE_BUY
        client.create_order(
            symbol=symbol,
            side=limit_side,
            type=ORDER_TYPE_LIMIT,
            quantity=quantity,
            price=f"{tp:.8f}",
            timeInForce=TIME_IN_FORCE_GTC
        )
        print(f"✅ Take Profit placé @ {tp:.8f}")

    except Exception as e:
        print("❌ Erreur lors de la création des ordres simples :", e)


def place_oco_order(side, entry_price, stop_loss, take_profit):
    """
    Passe un ordre MARKET puis crée un OCO TP/SL en utilisant 2 ordres simples.
    """
    try:
        # ---- PASSAGE DE L'ORDRE MARKET ----
        if side == "LONG":
            client.create_order(symbol=SYMBOL, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=QUANTITY)
            print(f"🟢 Achat MARKET passé @ {entry_price:.8f}")

            # ---- OCO via 2 ordres simples ----
            place_simple_orders(
                symbol=SYMBOL,
                side=SIDE_BUY,
                quantity=QUANTITY,
                sl=round_price(SYMBOL, stop_loss),
                tp=round_price(SYMBOL, take_profit)
            )

        elif side == "SHORT":
            client.create_order(symbol=SYMBOL, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=QUANTITY)
            print(f"🔴 Vente MARKET passée @ {entry_price:.8f}")

            place_simple_orders(
                symbol=SYMBOL,
                side=SIDE_SELL,
                quantity=QUANTITY,
                sl=round_price(SYMBOL, stop_loss),
                tp=round_price(SYMBOL, take_profit)
            )

        print(f"OCO (TP/SL) construit via 2 ordres simples pour {side}")

    except BinanceAPIException as e:
        print("❌ Erreur lors de la création de l'ordre :", e)


def strategy():
    """Stratégie principale"""
    global open_position, entry_price, stop_loss, take_profit, cycle_count

    try:
        bids, asks = get_orderbook(SYMBOL)
        supports, resistances = detect_levels(bids, asks)
        last_price = float(client.get_symbol_ticker(symbol=SYMBOL)['price'])
    except BinanceAPIException as e:
        print("Erreur API :", e)
        return

    cycle_count += 1

    # Affichage toutes les PRINT_EVERY cycles
    if cycle_count % PRINT_EVERY == 0:
        print(f"\n📊 Cycle {cycle_count}")
        print(f"Prix actuel : {last_price:.8f}")
        print(f"Supports forts : {supports[:10]}")
        print(f"Résistances fortes : {resistances[:10]}")

    if open_position is None:
        # ---- SIGNAL ACHAT ----
        if supports and last_price <= supports[0] * 1.001:
            open_position = "LONG"
            entry_price = last_price
            stop_loss = supports[0] * 0.999
            take_profit = entry_price + (entry_price - stop_loss) * RISK_REWARD
            print(f"🟢 Achat ouvert @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f}")
            place_oco_order("LONG", entry_price, stop_loss, take_profit)

        # ---- SIGNAL VENTE ----
        elif resistances and last_price >= resistances[0] * 0.999:
            open_position = "SHORT"
            entry_price = last_price
            stop_loss = resistances[0] * 1.001
            take_profit = entry_price - (stop_loss - entry_price) * RISK_REWARD
            print(f"🔴 Vente ouverte @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f}")
            place_oco_order("SHORT", entry_price, stop_loss, take_profit)

    else:
        # Affiche position en cours
        print(f"📌 Position en cours : {open_position} @ {entry_price:.8f} | SL = {stop_loss:.8f} | TP = {take_profit:.8f}")

# ==== BOUCLE PRINCIPALE ====
if __name__ == "__main__":
    try:
        afficher_soldes()
        while True:
            strategy()
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nArrêt manuel du bot.")
        afficher_soldes()
