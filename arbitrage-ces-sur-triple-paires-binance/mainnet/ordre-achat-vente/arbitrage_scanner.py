from decimal import Decimal
import time
from paire import Paire
from binance_client import BinanceClient
from mock_paire import MockPaire
from datetime import datetime

class ArbitrageScanner:
    """
    Scrute les prix de trois paires pour générer un signal d'arbitrage.
    """
    def __init__(self, usdc1: Paire, inter: Paire, usdc2: Paire, capital: Decimal = Decimal("100"), seuilUsdc: Decimal = Decimal("1")):
        """
        :param paire1, paire2, paire3: instances de Paire ou MockPaire
        :param seuil_profitPourcent: seuil minimum de profit (%) pour générer un signal
        """
        self.usdc1 = usdc1
        self.inter = inter
        self.usdc2 = usdc2
        self.capital = capital
        self.seuilUsdc = Decimal(seuilUsdc)

    def simulate_aller(self, prixUsdc1: Decimal, prixInter:Decimal, prixUsdc2: Decimal):
        """
        USDC -> intermédiaire -> autre crypto -> USDC
        Exemple : USDC -> ETH -> BTC -> USDC
        """
        inter_amount = self.capital / prixUsdc1       # USDC -> crypto1
        inter_to_other = inter_amount * prixInter  # crypto1 -> crypto2
        finalUsdc = inter_to_other * prixUsdc2   # crypto2 -> USDC
        profit = finalUsdc - self.capital
        profitPourcent = (profit / self.capital) * 100

        prixUsdc1 = self.usdc1.prix
        prixUsdc1 = self.usdc1.prix
        return prixUsdc1, prixInter, prixUsdc2, finalUsdc, profit, profitPourcent

    def simulate_retour(self, prixUsdc1: Decimal, prixInter:Decimal, prixUsdc2: Decimal):
        """
        USDC -> autre crypto -> intermédiaire -> USDC
        Exemple : USDC -> BTC -> ETH -> USDC
        """
        other_amount = self.capital / prixUsdc2         # USDC -> crypto2
        other_to_inter = other_amount / prixInter  # crypto2 -> crypto1
        finalUsdc = other_to_inter * prixUsdc1    # crypto1 -> USDC
        profit = finalUsdc - self.capital
        profitPourcent = (profit / self.capital) * 100

        return prixUsdc1, prixInter, prixUsdc2, finalUsdc, profit, profitPourcent

    def scan(self) -> dict:
        """
        Scrute les prix et renvoie un dictionnaire avec le signal et le profit théorique.
        :param montant_initial: montant en quote de la première paire
        :return: dictionnaire avec info et signal
        """
        prixUsdc1 = self.usdc1.prix
        prixInter = self.inter.prix
        prixUsdc2 = self.usdc2.prix
        
        prixUsdc1, prixInter, prixUsdc2, finalUsdc, profit_aller, profitPourcent = self.simulate_aller(prixUsdc1, prixInter, prixUsdc2)
        prixUsdc1, prixInter, prixUsdc2, finalUsdc, profit_retour, profitPourcent = self.simulate_retour(prixUsdc1, prixInter, prixUsdc2)

        signal = None
        profit = 0.0
        if profit_aller >= self.seuilUsdc :
                profit = profit_aller
                signal = "ALLER"

        if profit_retour >= self.seuilUsdc :
                profit = profit_retour
                signal = "RETOUR"

        # timestamp en millisecondes
        ts_millis = int(datetime.now().timestamp() * 1000)
    
        return {
            "timestamp": ts_millis,
            "prix": {
                "prixUsdc1": f"{prixUsdc1:.8f}",
                "prixInter": f"{prixInter:.8f}",
                "prixUsdc2" : f"{prixUsdc2:.8f}",
            },
            "finalUsdc": f"{finalUsdc:.8f}",
            "profitPourcent": f"{profitPourcent:.8f}",
            "profit": f"{profit:.8f}",
            "signal": signal
        }



if __name__ == "__main__":

    with BinanceClient() as binance:
        # Création de paires mock pour test
        # ['SKLUSDC', 'SKLBTC', 'BTCUSDC'] 
        # p1 = MockPaire(Paire(binance.client, "SKLUSDC"))
        # p2 = MockPaire(Paire(binance.client, "SKLBTC"))
        # p3 = MockPaire(Paire(binance.client, "BTCUSDC"))

        p1 = Paire(binance.client, "SKLUSDC")
        p2 = Paire(binance.client, "SKLBTC")
        p3 = Paire(binance.client, "BTCUSDC")

        scanner = ArbitrageScanner(p1, p2, p3)

        while True:
            result = scanner.scan()  # 1000 USDC en quote initial
            import json
            #print(json.dumps(result, indent=4))
            print(json.dumps(result))
            time.sleep(5)