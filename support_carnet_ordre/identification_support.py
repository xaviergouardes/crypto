import pandas as pd
import matplotlib.pyplot as plt
from binance.client import Client
import os
import time

# ==== CONFIG ====
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = "ETHBTC"
LIMIT = 200          # nombre d'ordres à récupérer
CLUSTER_STEP = 0.0005  # regrouper les prix proches
MIN_RATIO = 0.05       # minimum % du volume total pour être considéré
TOP_N = 8              # nombre de zones clés à afficher

client = Client(API_KEY, API_SECRET)

# ==== Récupération carnet d'ordres ====
def get_order_book(symbol, limit=200):
    book = client.get_order_book(symbol=symbol, limit=limit)
    bids = pd.DataFrame(book['bids'], columns=['price','qty']).astype(float)
    asks = pd.DataFrame(book['asks'], columns=['price','qty']).astype(float)
    return bids, asks

# ==== Clustering des prix proches ====
def cluster_orders(df, step=0.0005):
    df['cluster'] = (df['price'] / step).round() * step
    grouped = df.groupby('cluster')['qty'].sum().reset_index()
    return grouped

# ==== Filtrage des zones significatives ====
def filter_significant_zones(df, min_ratio=0.05):
    total_qty = df['qty'].sum()
    significant = df[df['qty']/total_qty >= min_ratio]
    return significant

# ==== Obtenir top N zones ====
def get_top_zones(df, top_n=8, reverse=False):
    sorted_df = df.sort_values('qty', ascending=reverse)
    return sorted_df['cluster'].head(top_n).tolist()

# ==== Affichage graphique ====
def plot_order_book(bids, asks, supports, resistances):
    plt.clf()
    plt.bar(bids['price'], bids['qty'], color='green', alpha=0.3, label='Bids')
    plt.bar(asks['price'], asks['qty'], color='red', alpha=0.3, label='Asks')

    for s in supports:
        plt.axvline(x=s, color='blue', linestyle='--', label='Support' if s==supports[0] else "")
    for r in resistances:
        plt.axvline(x=r, color='orange', linestyle='--', label='Resistance' if r==resistances[0] else "")

    plt.xlabel("Prix")
    plt.ylabel("Quantité")
    plt.title(f"Carnet d'ordres {SYMBOL} - Supports/Résistances clés")
    plt.legend()
    plt.pause(0.1)

if __name__ == "__main__":
    plt.ion()  # mode interactif pour mise à jour live
    fig = plt.figure(figsize=(12,6))
    try:
        while True:
            bids, asks = get_order_book(SYMBOL, LIMIT)
            bids_clustered = cluster_orders(bids, CLUSTER_STEP)
            asks_clustered = cluster_orders(asks, CLUSTER_STEP)

            bids_sig = filter_significant_zones(bids_clustered, MIN_RATIO)
            asks_sig = filter_significant_zones(asks_clustered, MIN_RATIO)

            supports = get_top_zones(bids_sig, TOP_N, reverse=True)  # descending pour supports
            resistances = get_top_zones(asks_sig, TOP_N, reverse=False)

            print("Supports clés :", supports)
            print("Résistances clés :", resistances)

            plot_order_book(bids, asks, supports, resistances)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nScript interrompu. Bye 👋")
        plt.ioff()
        plt.show()
