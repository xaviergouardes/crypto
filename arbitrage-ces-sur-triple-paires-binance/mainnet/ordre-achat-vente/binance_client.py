import os
from binance.client import Client
import logging
import logging.config

logger = logging.getLogger("binance_client")

class BinanceClient:
    """
    Classe qui encapsule les clés API et crée un client Binance.
    Les clés sont lues automatiquement dans les variables d'environnement :
        - BINANCE_API_KEY
        - BINANCE_API_SECRET
    
    Utilisable comme contexte avec 'with'.
    """

    def __init__(self, testnet=True):
        self.__api_key = os.getenv("BINANCE_API_KEY")
        self.__api_secret = os.getenv("BINANCE_API_SECRET")
        self.__testnet = testnet

        if not self.__api_key or not self.__api_secret:
            raise ValueError("Les variables d'environnement BINANCE_API_KEY et BINANCE_API_SECRET doivent être définies.")

        self.client = None

    def __enter__(self):
        self.client = Client(self.__api_key, self.__api_secret, testnet=self.__testnet)
        #logger.info(f"Client Binance sur {'TESTNET' if self.__testnet else 'MAINNET'}")
        logger.info("#### TOTO")
        print(f"Client Binance sur {'TESTNET' if self.__testnet else 'MAINNET'}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client = None
        return False  # ne supprime pas les exceptions


if __name__ == "__main__":
    
    try:
        with BinanceClient() as binance:
            # Exemple rapide : récupération du solde
            account_info = binance.client.get_account()
            balances = account_info.get("balances", [])
            
            print("Connexion réussie ✅")
            print("Extrait des soldes (token non nul uniquement) :")
            for b in balances:
                free = float(b["free"])
                locked = float(b["locked"])
                if free > 0 or locked > 0:
                    print(f" - {b['asset']}: libre={free}, bloqué={locked}")
    except Exception as e:
        print("Erreur lors du test BinanceClient ❌")
        print(e)
