# triangular_arbitrage_param.py
from binance.client import Client
from decimal import Decimal, getcontext
import time
from datetime import datetime
import os

# Augmenter la précision
getcontext().prec = 10

# Configuration API Binance

API_KEY = os.environ.get("BINANCE_API_KEY")
print("===> " , API_KEY)
API_SECRET = os.environ.get("BINANCE_API_SECRET")

#client = Client(API_KEY, API_SECRET)
client = Client(None, None)

# Capital simulé
CAPITAL_USDC = Decimal("100")

# === PARAMÈTRES ===
# Triplette à analyser
# ['ETHUSDC', 'ETHBTC', 'BTCUSDC']
# ['PLUMEUSDC', 'PLUMETRY', 'USDCTRY']
# ['SKLUSDC', 'SKLBTC', 'BTCUSDC'] => marche bien
# ['ACHUSDC', 'ACHBTC', 'BTCUSDC']
# ['WCTUSDC', 'WCTTRY', 'USDCTRY']
PAIR_USDC_1 = "SKLUSDC"
PAIR_INTER = "SKLBTC"
PAIR_USDC_2 = "BTCUSDC"

# Fonction pour récupérer le prix d'un symbole
def get_price(symbol):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return Decimal(ticker['price'])

def simulate_aller(usdc1, inter, usdc2, capital=CAPITAL_USDC):
    """
    USDC -> intermédiaire -> autre crypto -> USDC
    Exemple : USDC -> ETH -> BTC -> USDC
    """
    inter_amount = capital / usdc1       # USDC -> crypto1
    inter_to_other = inter_amount * inter  # crypto1 -> crypto2
    final_usdc = inter_to_other * usdc2   # crypto2 -> USDC
    profit = final_usdc - capital
    profit_pct = (profit / capital) * 100
    return final_usdc, profit, profit_pct

def simulate_retour(usdc1, inter, usdc2, capital=CAPITAL_USDC):
    """
    USDC -> autre crypto -> intermédiaire -> USDC
    Exemple : USDC -> BTC -> ETH -> USDC
    """
    other_amount = capital / usdc2         # USDC -> crypto2
    other_to_inter = other_amount / inter  # crypto2 -> crypto1
    final_usdc = other_to_inter * usdc1    # crypto1 -> USDC
    profit = final_usdc - capital
    profit_pct = (profit / capital) * 100
    return final_usdc, profit, profit_pct

def main_loop():
    while True:
        try:
            # Récupérer les prix en live
            price_usdc_1 = get_price(PAIR_USDC_1)
            price_usdc_2 = get_price(PAIR_USDC_2)
            price_inter = get_price(PAIR_INTER)

            # Simulations
            final_aller, profit_aller, pct_aller = simulate_aller(price_usdc_1, price_inter, price_usdc_2)
            final_retour, profit_retour, pct_retour = simulate_retour(price_usdc_1, price_inter, price_usdc_2)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Affichage
            if profit_aller > 0:
                print(f"{timestamp} | {PAIR_USDC_1}={price_usdc_1:.2f} | {PAIR_INTER}={price_inter:.12f} | {PAIR_USDC_2}={price_usdc_2:.2f}  | "
                      f"[ALLER] USDC final={final_aller:.2f} Profit={profit_aller:.2f} ({pct_aller:.2f}%) ")
                
            if profit_retour > 0:
                 print(f"{timestamp} | {PAIR_USDC_1}={price_usdc_1:.2f} | {PAIR_INTER}={price_inter:.12f} | {PAIR_USDC_2}={price_usdc_2:.2f}  | "
                      f"[RETOUR] USDC final={final_retour:.2f} Profit={profit_retour:.2f} ({pct_retour:.2f}%)")
                 
            time.sleep(5)

        except Exception as e:
            print("Erreur :", e)
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
