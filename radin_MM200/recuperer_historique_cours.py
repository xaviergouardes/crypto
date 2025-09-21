import pandas as pd
from binance.client import Client
import os

# ==== CONFIG ====
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = "ETHBTC"
#INTERVAL = Client.KLINE_INTERVAL_1HOUR  # 1 minute, 5 minutes, 1h, 1d...
INTERVAL = Client.KLINE_INTERVAL_3MINUTE  # 1 minute, 5 minutes, 1h, 1d...
START_DATE = "1 Jan, 2023"
END_DATE = "20 Sep, 2025"

client = Client(API_KEY, API_SECRET)

# ==== Récupération historique ====
klines = client.get_historical_klines(SYMBOL, INTERVAL, START_DATE, END_DATE)

# ==== Transformation en DataFrame ====
df = pd.DataFrame(klines, columns=[
    "timestamp", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
])

# Convertir timestamp et colonnes float
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)

# Sauvegarder en CSV
df.to_csv("ETHBTC_historique.csv", index=False)
print("Historique téléchargé et sauvegardé dans ETHBTC_historique.csv")
