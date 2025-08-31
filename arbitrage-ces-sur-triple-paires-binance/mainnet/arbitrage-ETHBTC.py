# triangular_arbitrage_live.py
from binance.client import Client
from decimal import Decimal, getcontext
import time
import os


# Augmenter la précision
getcontext().prec = 10

client = Client(None, None)

# Capital simulé
CAPITAL_USDC = Decimal("1000")

# Fonction pour récupérer le prix d'un symbole
def get_price(symbol):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return Decimal(ticker['price'])

def simulate_aller(eth_usdc, btc_usdc, eth_btc, capital=CAPITAL_USDC):
    """USDC -> ETH -> BTC -> USDC"""
    eth = capital / eth_usdc
    btc = eth * eth_btc
    final_usdc = btc * btc_usdc
    profit = final_usdc - capital
    profit_pct = (profit / capital) * 100
    return final_usdc, profit, profit_pct

def simulate_retour(eth_usdc, btc_usdc, eth_btc, capital=CAPITAL_USDC):
    """USDC -> BTC -> ETH -> USDC"""
    btc = capital / btc_usdc
    eth = btc / eth_btc
    final_usdc = eth * eth_usdc
    profit = final_usdc - capital
    profit_pct = (profit / capital) * 100
    return final_usdc, profit, profit_pct

def main_loop():
    while True:
        try:
            # Récupérer les prix en live
            eth_usdc = get_price("ETHUSDC")
            btc_usdc = get_price("BTCUSDC")
            eth_btc = get_price("ETHBTC")

            # Simulations
            final_aller, profit_aller, pct_aller = simulate_aller(eth_usdc, btc_usdc, eth_btc)
            final_retour, profit_retour, pct_retour = simulate_retour(eth_usdc, btc_usdc, eth_btc)

            # Affichage sur une seule ligne
            print(
                f"ETH/USDC={eth_usdc:.2f} | BTC/USDC={btc_usdc:.2f} | ETH/BTC={eth_btc:.5f} | "
                f"[ALLER] USDC final={final_aller:.2f} Profit={profit_aller:.2f} ({pct_aller:.2f}%) | "
                f"[RETOUR] USDC final={final_retour:.2f} Profit={profit_retour:.2f} ({pct_retour:.2f}%)"
            )

            time.sleep(5)  # rafraîchissement toutes les 5 secondes

        except Exception as e:
            print("Erreur :", e)
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
