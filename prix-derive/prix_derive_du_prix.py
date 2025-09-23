import time
from binance.client import Client
import numpy as np

# ==== CONFIGURATION ====
SYMBOL = "ETHUSDC"   # Paire à analyser
INTERVAL = 5         # Intervalle entre mesures en secondes
WINDOW = 25          # Nombre de points pour calculer la dérivée moyenne

# ==== CLIENT PUBLIC BINANCE ====
client = Client()  # Lecture publique seulement

# ==== VARIABLES ====
prices = []

def get_price(symbol):
    """Récupère le dernier prix de la paire"""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

def calc_derivative(prices):
    """
    Calcule la dérivée numérique comme moyenne des différences
    prices : liste de prix
    Retourne la dérivée moyenne
    """
    if len(prices) < 2:
        return 0.0
    diffs = np.diff(prices)
    return np.mean(diffs) / INTERVAL  # variation par seconde

# ==== BOUCLE PRINCIPALE ====
try:
    while True:
        price = get_price(SYMBOL)
        prices.append(price)
        # On conserve seulement les derniers WINDOW points
        if len(prices) > WINDOW:
            prices.pop(0)

        derivative = calc_derivative(prices)

        print(f"Prix actuel : {price:.6f} | Dérivée (Δprix/s) : {derivative:.6f}")

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\nArrêt manuel.")
