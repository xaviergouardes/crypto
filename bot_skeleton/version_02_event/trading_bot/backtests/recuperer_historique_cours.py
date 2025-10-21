import pandas as pd
from binance.client import Client
import os
from datetime import datetime

# ==== CONFIG ====
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = "BTCUSDC"
# INTERVAL = Client.KLINE_INTERVAL_3MINUTE  # période dynamique
INTERVAL = Client.KLINE_INTERVAL_5MINUTE  # période dynamique
START_DATE = "20250701"  # format AAAAMMJJ
END_DATE = "20251019"    # format AAAAMMJJ

# ==== Conversion pour Binance ====
start_for_binance = datetime.strptime(START_DATE, "%Y%m%d").strftime("%d %b, %Y")
end_for_binance = datetime.strptime(END_DATE, "%Y%m%d").strftime("%d %b, %Y")

# ==== Connexion Binance ====
client = Client(API_KEY, API_SECRET)

# ==== Récupération historique ====
print(f"Téléchargement de l'historique {SYMBOL} ({INTERVAL}) du {START_DATE} au {END_DATE} ...")
klines = client.get_historical_klines(SYMBOL, INTERVAL, start_for_binance, end_for_binance)
print("Téléchargement terminé.")

# ==== Transformation en DataFrame ====
df = pd.DataFrame(klines, columns=[
    "timestamp", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
])

# Conversion des timestamps et colonnes numériques
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

# ==== Construction dynamique du nom de fichier ====
interval_clean = INTERVAL.lower().replace("kline_interval_", "").replace("client.", "")
# Exemple : "3m", "1h", "1d", etc.
interval_suffix = INTERVAL.replace("KLINE_INTERVAL_", "").lower()

repertoire_script = os.path.dirname(os.path.abspath(__file__))
nom_fichier = f"{SYMBOL}_{interval_suffix}_historique_{START_DATE}_{END_DATE}.csv"
chemin_csv = os.path.join(repertoire_script, nom_fichier)

# ==== Sauvegarde ====
df.to_csv(chemin_csv, index=False)
print(f"Historique sauvegardé dans : {nom_fichier}")
