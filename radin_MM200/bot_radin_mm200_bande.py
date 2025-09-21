import os
import time
import signal
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import ta

# === CONFIG ===
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = "ETHBTC"
QTY = 0.01  # quantité d’ETH
RISK_PCT = 0.0003  # 0.3% de risque par trade
RR = 1.5  # ratio Risk/Reward

client = Client(API_KEY, API_SECRET, testnet=True)

# === Position tracking ===
position = {
    "en_position": False,
    "side": None,
    "entry": None,
    "sl": None,
    "tp": None
}

# === Affichage des soldes ===
def afficher_soldes():
    balances = client.get_account()["balances"]
    for asset in ["ETH", "BTC"]:
        balance = next(b for b in balances if b["asset"] == asset)
        print(f"{asset}: libre={balance['free']} verrouillé={balance['locked']}")

# === Gestion Ctrl+C ===
def handle_exit(sig, frame):
    print("\n⛔ Interruption détectée. État final des soldes :")
    afficher_soldes()
    exit(0)

signal.signal(signal.SIGINT, handle_exit)

# === Récupération des données ===
def get_data(symbol, interval="1m", lookback="300"):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=int(lookback))
    df = pd.DataFrame(klines, columns=[
        "timestamp","open","high","low","close","volume",
        "close_time","qav","num_trades","taker_base_vol",
        "taker_quote_vol","ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

# === Vérification du signal ===
def check_signal(df):
    df["MA200"] = ta.trend.sma_indicator(df["close"], window=200)
    last_close = df["close"].iloc[-1]
    last_ma200 = df["MA200"].iloc[-1]
    if last_close > last_ma200:
        return "BUY", last_close
    elif last_close < last_ma200:
        return "SELL", last_close
    else:
        return None, None

# === Passage d’ordre ===
def entrer_position(signal, prix):
    global position
    try:
        if signal == "BUY" and not position["en_position"]:
            order = client.create_order(
                symbol=SYMBOL,
                side="BUY",
                type="MARKET",
                quantity=QTY
            )
            print("Signal ACHAT ⚡")
            print("Ordre d’achat passé :", order)
            afficher_soldes()

            sl = prix * (1 - RISK_PCT)
            tp = prix * (1 + RISK_PCT * RR)
            position = {"en_position": True, "side": "BUY", "entry": prix, "sl": sl, "tp": tp}
            print(f"🎯 TP fixé à {tp:.8f}, 🛑 SL fixé à {sl:.8f}")

        elif signal == "SELL" and not position["en_position"]:
            order = client.create_order(
                symbol=SYMBOL,
                side="SELL",
                type="MARKET",
                quantity=QTY
            )
            print("Signal VENTE 🔻")
            print("Ordre de vente passé :", order)
            afficher_soldes()

            sl = prix * (1 + RISK_PCT)
            tp = prix * (1 - RISK_PCT * RR)
            position = {"en_position": True, "side": "SELL", "entry": prix, "sl": sl, "tp": tp}
            print(f"🎯 TP fixé à {tp:.8f}, 🛑 SL fixé à {sl:.8f}")

        else:
            print("Aucun ordre : déjà en position.")

    except BinanceAPIException as e:
        print("Erreur :", e)

# === Vérification TP / SL ===
def verifier_tp_sl(last_price):
    global position
    if not position["en_position"]:
        return

    if position["side"] == "BUY":
        if last_price <= position["sl"]:
            print(f"🛑 Stop Loss atteint ({last_price:.8f}) → VENTE")
            fermer_position("SELL")
        elif last_price >= position["tp"]:
            print(f"🎯 Take Profit atteint ({last_price:.8f}) → VENTE")
            fermer_position("SELL")

    elif position["side"] == "SELL":
        if last_price >= position["sl"]:
            print(f"🛑 Stop Loss atteint ({last_price:.8f}) → RACHAT")
            fermer_position("BUY")
        elif last_price <= position["tp"]:
            print(f"🎯 Take Profit atteint ({last_price:.8f}) → RACHAT")
            fermer_position("BUY")

# === Fermeture de position ===
def fermer_position(action):
    global position
    try:
        order = client.create_order(
            symbol=SYMBOL,
            side=action,
            type="MARKET",
            quantity=QTY
        )
        print("Position fermée :", order)
        afficher_soldes()
        position = {"en_position": False, "side": None, "entry": None, "sl": None, "tp": None}
    except BinanceAPIException as e:
        print("Erreur fermeture :", e)

# === MAIN LOOP ===
if __name__ == "__main__":
    print("=== Bot Radin MM200 lancé ===")
    print("💰 Soldes initiaux :")
    afficher_soldes()

    while True:
        try:
            df = get_data(SYMBOL)
            signal, prix = check_signal(df)

            last_price = df["close"].iloc[-1]

            if position["en_position"]:
                verifier_tp_sl(last_price)
            else:
                if signal:
                    entrer_position(signal, prix)

            time.sleep(60)  # 1 minute entre deux checks
        except Exception as e:
            print("Erreur inattendue :", e)
            time.sleep(10)
