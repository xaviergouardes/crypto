import pandas as pd
from binance.client import Client
import os
import time

# ==== CONFIGURATION ====
API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
API_SECRET = os.getenv("BINANCE_TESTNET_API_SECRET")
SYMBOL = "ETHBTC"
LIMIT = 200
CLUSTER_STEP = 0.0005   # regroupe les prix proches
MIN_RATIO = 0.05        # volume minimal relatif pour être considéré comme support/résistance
TOP_N = 8               # nombre de niveaux clés à retenir
TOLERANCE = 0.001       # 0.1% autour du niveau
RATIO_TP_SL = 1.5       # ratio take profit / stop loss
QUANTITY = 0.01         # quantité à trader
REAL_TRADING = False    # False pour testnet/paper trading

# ==== Connexion Binance (testnet) ====
client = Client(API_KEY, API_SECRET, testnet=True)

# ==== Fonctions ====
def get_order_book(symbol, limit=200):
    """ Récupère le carnet d'ordres """
    book = client.get_order_book(symbol=symbol, limit=limit)
    bids = pd.DataFrame(book['bids'], columns=['price','qty']).astype(float)
    asks = pd.DataFrame(book['asks'], columns=['price','qty']).astype(float)
    return bids, asks

def cluster_orders(df, step=0.0005):
    """ Regroupe les ordres proches pour former des zones """
    df['cluster'] = (df['price'] / step).round() * step
    grouped = df.groupby('cluster')['qty'].sum().reset_index()
    return grouped

def filter_significant_zones(df, min_ratio=0.05):
    """ Filtre les zones avec volume significatif """
    total_qty = df['qty'].sum()
    significant = df[df['qty']/total_qty >= min_ratio]
    return significant

def get_top_zones(df, top_n=8, reverse=False):
    """ Garde les top N zones """
    sorted_df = df.sort_values('qty', ascending=reverse)
    return sorted_df['cluster'].head(top_n).tolist()

def get_last_price(symbol):
    """ Récupère le dernier prix """
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

def place_order(signal, price, sl, tp):
    """ Place un ordre BUY/SELL avec SL et TP """
    if not REAL_TRADING:
        print(f"[TEST] Signal {signal} à {price:.6f} | SL={sl:.6f} TP={tp:.6f}")
        return

    if signal == "BUY":
        order = client.create_order(
            symbol=SYMBOL,
            side="BUY",
            type="MARKET",
            quantity=QUANTITY
        )
        # OCO pour TP/SL
        client.create_oco_order(
            symbol=SYMBOL,
            side="SELL",
            quantity=QUANTITY,
            price=str(round(tp,8)),
            stopPrice=str(round(sl,8)),
            stopLimitPrice=str(round(sl,8)),
            stopLimitTimeInForce="GTC"
        )
    elif signal == "SELL":
        order = client.create_order(
            symbol=SYMBOL,
            side="SELL",
            type="MARKET",
            quantity=QUANTITY
        )
        client.create_oco_order(
            symbol=SYMBOL,
            side="BUY",
            quantity=QUANTITY,
            price=str(round(tp,8)),
            stopPrice=str(round(sl,8)),
            stopLimitPrice=str(round(sl,8)),
            stopLimitTimeInForce="GTC"
        )

    print(f"Ordre {signal} exécuté : {order}")

# ==== Boucle principale ====
if __name__ == "__main__":
    try:
        print("=== Bot de trading basé sur supports/résistances lancé ===")
        while True:
            bids, asks = get_order_book(SYMBOL, LIMIT)
            bids_clustered = cluster_orders(bids, CLUSTER_STEP)
            asks_clustered = cluster_orders(asks, CLUSTER_STEP)

            bids_sig = filter_significant_zones(bids_clustered, MIN_RATIO)
            asks_sig = filter_significant_zones(asks_clustered, MIN_RATIO)

            supports = get_top_zones(bids_sig, TOP_N, reverse=True)
            resistances = get_top_zones(asks_sig, TOP_N, reverse=False)

            prix = get_last_price(SYMBOL)
            print(f"\nPrix actuel : {prix:.6f}")
            print("Supports :", supports)
            print("Résistances :", resistances)

            # Signaux BUY
            for s in supports:
                if abs(prix - s)/s <= TOLERANCE:
                    sl = s * (1 - 0.001)  # stop juste sous le support
                    tp = prix + (prix - sl) * RATIO_TP_SL
                    place_order("BUY", prix, sl, tp)

            # Signaux SELL
            for r in resistances:
                if abs(prix - r)/r <= TOLERANCE:
                    sl = r * (1 + 0.001)  # stop juste au-dessus
                    tp = prix - (sl - prix) * RATIO_TP_SL
                    place_order("SELL", prix, sl, tp)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nScript interrompu. Bye 👋")
