from binance.client import Client
import os

# Remplace par tes propres clés API
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Initialise le client Binance
client = Client(API_KEY, API_SECRET, testnet=True)

# Liste des cryptos à vérifier
cryptos = ["BTC", "ACH", "USDC", "SKL", "ETH"]

try:
    # Récupération des informations de compte
    account_info = client.get_account()
    balances = account_info['balances']

    # Parcours des cryptos pour afficher le solde disponible
    for crypto in cryptos:
        balance_info = next((item for item in balances if item['asset'] == crypto), None)
        if balance_info:
            free = float(balance_info['free'])
            locked = float(balance_info['locked'])
            print(f"{crypto} - Disponible: {free}, Bloqué: {locked}")
        else:
            print(f"{crypto} - Non trouvé dans le compte.")

except Exception as e:
    print("Erreur lors de la récupération des soldes :", e)
