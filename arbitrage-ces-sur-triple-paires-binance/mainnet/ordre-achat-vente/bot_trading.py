from binance_client import BinanceClient
from decimal import Decimal
from paire import Paire
from mock_paire import MockPaire
from arbitrage_scanner import ArbitrageScanner
from order_engine import OrderEngine
import time
import json
from datetime import datetime

class BotTrading:
    def __init__(self, usdc1: Paire, inter: Paire, usdc2: Paire, capital: Decimal = Decimal("100"), seuilUsdc: Decimal = Decimal("1")):
        
        self.scanner = ArbitrageScanner(usdc1, inter, usdc2, capital=capital, seuilUsdc=seuilUsdc)
        self.order_engine = OrderEngine(usdc1, inter, usdc2, capital=capital)
        self.capital = capital

    def scan_and_trade(self, iterations: int | None = None):
            """Boucle principale : scruter le marché et simuler les trades ALLER uniquement."""
            count = 0
            while iterations is None or count < iterations:
                try:
                    
                    signal_data = self.scanner.scan()
                    signal = signal_data["signal"]

                    orders = []
                    if signal == "ALLER":
                        orders = self.order_engine.execute_trade_aller()
                        #print(order1)

                    if signal == "RETOUR":
                        orders = self.order_engine.execute_trade_retour()
                        #print(order1)

                    time.sleep(5)
                    count += 1

                except Exception as e:
                    print("Erreur dans le scan/trade:", e)
                    raise e
                    time.sleep(5)
            
            result = {
                "signal_data": signal_data,
                "orders": orders
            }

            return result

    def log_trade(self, result: dict, filename="./trades.json"):
        # Ajoute un horodatage dans les données
        result_with_time = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            **result
        }

        # Écrit dans le fichier en mode append (chaque trade sur une ligne JSON)
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(result_with_time, ensure_ascii=False) + "\n")

        # Affiche joliment à l’écran
        print(json.dumps(result_with_time, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    # PAIRS = ["SKLUSDC", "SKLBTC", "BTCUSDC"]
    with BinanceClient() as binance:
        #p1 = Paire(binance.client, "SKLUSDC")
        #p2 = Paire(binance.client, "SKLBTC")
        #p3 = Paire(binance.client, "BTCUSDC")

        p1 = MockPaire(Paire(binance.client, "SKLUSDC"))
        p2 = MockPaire(Paire(binance.client, "SKLBTC"))
        p3 = MockPaire(Paire(binance.client, "BTCUSDC"))

        bot = BotTrading(p1, p2, p3)
        result = bot.scan_and_trade(1)
        bot.log_trade(result)