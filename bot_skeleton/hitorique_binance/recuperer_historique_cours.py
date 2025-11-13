import os
from datetime import datetime
import pandas as pd
from binance.client import Client

# ==== CONFIG ====
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = "ETHUSDC"
INTERVAL = Client.KLINE_INTERVAL_5MINUTE  # Ex : 5 minutes
START_DATE = "20250914"
END_DATE = "20251114"
TIMEZONE = "Europe/Paris"  # Fuseau horaire local

# ==== Conversion pour Binance ====
start_for_binance = datetime.strptime(START_DATE, "%Y%m%d").strftime("%d %b, %Y")
end_for_binance = datetime.strptime(END_DATE, "%Y%m%d").strftime("%d %b, %Y")

# ==== Connexion Binance ====
client = Client(API_KEY, API_SECRET)

# ==== Récupération historique OHLC ====
print(f"Téléchargement de l'historique {SYMBOL} ({INTERVAL}) du {START_DATE} au {END_DATE} ...")
klines = client.get_historical_klines(SYMBOL, INTERVAL, start_for_binance, end_for_binance)
print("Téléchargement terminé.")

# ==== Transformation en DataFrame ====
df = pd.DataFrame(klines, columns=[
    "timestamp", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
])

# Conversion des colonnes numériques
for col in ["open", "high", "low", "close", "volume"]:
    df[col] = df[col].astype(float)

# Conversion des timestamps en datetime UTC puis fuseau local
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
df["timestamp_local"] = df["timestamp"].dt.tz_convert(TIMEZONE)
df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True).dt.tz_convert(TIMEZONE)

# ==== Ajout du dernier prix en direct ====
# last_prices = []
# for ts in df["timestamp"]:
#     ticker = client.get_symbol_ticker(symbol=SYMBOL)
#     last_prices.append(float(ticker["price"]))
# df["last_price"] = last_prices

# ==== Construction dynamique du nom de fichier ====
interval_suffix = INTERVAL.replace("KLINE_INTERVAL_", "").lower()
repertoire_script = os.path.dirname(os.path.abspath(__file__))
nom_fichier = f"{SYMBOL}_{interval_suffix}_historique_{START_DATE}_{END_DATE}.csv"
chemin_csv = os.path.join(repertoire_script, nom_fichier)

# ==== Sauvegarde ====
df.to_csv(chemin_csv, index=False)
print(f"Historique sauvegardé dans : {nom_fichier}")
