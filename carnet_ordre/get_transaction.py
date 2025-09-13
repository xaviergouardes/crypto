from binance.client import Client
from datetime import datetime
import os
import csv

# Clés API Testnet
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Initialisation du client Testnet
client = Client(API_KEY, API_SECRET, testnet=True)

# Paires à vérifier
pairs = ["BTCUSDC", "ACHUSDC", "ACHBTC"]

# Timestamp pour le début de la journée (00:00 aujourd'hui)
today = datetime.now()
start_time = int(datetime(today.year, today.month, today.day).timestamp() * 1000)

all_trades = []

for pair in pairs:
    last_id = None
    while True:
        try:
            # Récupération des trades depuis startTime et pagination par fromId
            if last_id:
                trades = client.get_my_trades(symbol=pair, fromId=last_id, startTime=start_time)
            else:
                trades = client.get_my_trades(symbol=pair, startTime=start_time)
            
            if not trades:
                break  # plus de trades à récupérer
            print(f"==== {trades[0]}")
            for trade in trades:
                all_trades.append({
                    "pair": pair,
                    "id": trade['id'],
                    "price": float(trade['price']),
                    "qty": float(trade['qty']),
                    "quoteQty": float(trade['quoteQty']),
                    "side": "Achat" if trade['isBuyer'] else "Vente",
                    "time": datetime.fromtimestamp(trade['time']/1000)
                })
            
            # Met à jour last_id pour la prochaine page
            last_id = trades[-1]['id'] + 1

        except Exception as e:
            print(f"Erreur pour {pair} :", e)
            break

# Tri par date/heure décroissante
all_trades.sort(key=lambda x: x['time'], reverse=True)

# Affichage clair
for trade in all_trades:
    print(f"{trade['time']} | {trade['pair']} | {trade['side']} | Prix: {trade['price']} | Quantité: {trade['qty']} | Quote Qty: {trade['quoteQty']} | ID: {trade['id']} ")

# Export CSV
# csv_file = "trades_testnet_today_desc.csv"
# with open(csv_file, mode='w', newline='') as file:
#     writer = csv.DictWriter(file, fieldnames=["time", "pair", "side", "price", "qty", "id"])
#     writer.writeheader()
#     for trade in all_trades:
#         writer.writerow({
#             "time": trade['time'],
#             "pair": trade['pair'],
#             "side": trade['side'],
#             "price": trade['price'],
#             "qty": trade['qty'],
#             "id": trade['id']
#         })

# print(f"\nToutes les transactions depuis aujourd'hui (anti-chronologique) ont été exportées dans {csv_file}")
