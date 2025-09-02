from binance_client import BinanceClient
from decimal import Decimal
from paire import Paire
from arbitrage_scanner import ArbitrageScanner
import time

class BotTrading:
    def __init__(self, usdc1: Paire, inter: Paire, usdc2: Paire, capital: Decimal = Decimal("100"), seuilUsdc: Decimal = Decimal("1")):
        
        self.scanner = ArbitrageScanner(usdc1, inter, usdc2, capital=capital, seuilUsdc= seuilUsdc)

    def scan_and_trade(self):
            """Boucle principale : scruter le marché et simuler les trades ALLER uniquement."""
            while True:
                #try:
                    result = self.scanner.scan()
                    print("==>", result)
                    prixUsdc1 = result["prix"]["prixUsdc1"]
                    prixInter = result["prix"]["prixInter"]
                    prixUsdc2 = result["prix"]["prixUsdc2"]
                    profit = result["profit"]
                    profitPourcent = result["profitPourcent"]
                    signal = result["signal"]

                    print(
                        f"[SCAN] Prix: USDC1={prixUsdc1}, Inter={prixInter}, USDC2={prixUsdc2} | "
                        f"Profit={profit} ({profitPourcent}%) | Signal={signal}"
                    )

                    #print(
                    #    f"[SCAN] Prix: USDC1={prixUsdc1:.8f}, Inter={prixInter:.8f}, USDC2={prixUsdc2:.8f} | "
                    #    f"Profit={profit:.8f} ({profitPourcent:.4f}%) | Signal={signal}"
                    #)

                    time.sleep(5)

                # except Exception as e:
                #     print("Erreur dans le scan/trade:", e)
                #     time.sleep(5)

if __name__ == "__main__":
    # PAIRS = ["SKLUSDC", "SKLBTC", "BTCUSDC"]
    with BinanceClient() as binance:
        p1 = Paire(binance.client, "SKLUSDC")
        p2 = Paire(binance.client, "SKLBTC")
        p3 = Paire(binance.client, "BTCUSDC")

        bot = BotTrading(p1, p2, p3)
        bot.scan_and_trade()