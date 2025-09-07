from binance_client import BinanceClient
from decimal import Decimal
from paire import Paire
from mock_paire import MockPaire
import time
import json
from datetime import datetime

class OrderEngine:
    def __init__(self, usdc1: Paire, inter: Paire, usdc2: Paire, capital: Decimal = Decimal("100")):
         self.usdc1 = usdc1
         self.inter = inter
         self.usdc2 = usdc2
         self.capital = capital


    def execute_trade_aller(self):
            # USDC -> Intermédiaire
            try:
                order1 = self.usdc1.buy_base_from_quote(self.capital)
                qty_base1 = Decimal(order1["executedQty"])
                self.log_binance_orders(order1, "execute_trade_aller_order1")

            except Exception as e:
                print("Erreur dans execute_trade_aller : order1", e)
                raise e

            # Intermédiaire -> Autre crypto
            try:
                order2 = self.inter.sell_base_get_quote(qty_base1)
                qty_base2 = Decimal(order2["cummulativeQuoteQty"])
                self.log_binance_orders(order2, "execute_trade_aller_order2")

            except Exception as e:
                print("Erreur dans execute_trade_aller : order2", e)
                raise e

            # Autre crypto -> USDC
            try:
                order3 = self.usdc2.sell_base_get_quote(qty_base2)
                final_usdc = Decimal(order3["cummulativeQuoteQty"])
                self.log_binance_orders(order3, "execute_trade_aller_order3")

            except Exception as e:
                print("Erreur dans execute_trade_aller : order3", e)
                raise e
            
            #print(f"[TRADE ALLER] Capital initial={self.capital}, Capital final={final_usdc:.8f}")

            return [order1, order2, order3]

    def execute_trade_retour(self):

            # USDC -> Autre crypto (BTC par ex.)
            try:
                order1 = self.usdc2.buy_base_from_quote(self.capital)
                qty_base1 = Decimal(order1["executedQty"])

            except Exception as e:
                print("Erreur dans execute_trade_retour : order2", e)
                raise e

            # Autre crypto -> Intermédiaire (ETH par ex.)
            try:
                order2 = self.inter.buy_base_from_quote(float(qty_base1))
                qty_base2 = Decimal(order2["executedQty"])

            except Exception as e:
                print("Erreur dans execute_trade_retour : order2", e)
                raise e
    
            # Intermédiaire -> USDC
            try:
                order3 = self.usdc1.sell_base_get_quote(qty_base2)
                final_usdc = Decimal(order3["cummulativeQuoteQty"])

            except Exception as e:
                print("Erreur dans execute_trade_retour : order2", e)
                raise e
    
            #print(f"[TRADE RETOUR] Capital initial={self.capital}, Capital final={final_usdc:.8f}")

            return [order1, order2, order3]

    def log_binance_orders(self, result: dict, order_num, filename="./binances_orders.json"):
        # Ajoute un horodatage dans les données
        result_with_time = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "order_num": order_num
            **result
        }

        # Écrit dans le fichier en mode append (chaque trade sur une ligne JSON)
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(result_with_time, ensure_ascii=False) + "\n")

        # Affiche joliment à l’écran
        print(json.dumps(result_with_time, ensure_ascii=False))


if __name__ == "__main__":
    # PAIRS = ["SKLUSDC", "SKLBTC", "BTCUSDC"]
    with BinanceClient() as binance:
        #p1 = Paire(binance.client, "SKLUSDC")
        #p2 = Paire(binance.client, "SKLBTC")
        #p3 = Paire(binance.client, "BTCUSDC")

        p1 = MockPaire(Paire(binance.client, "SKLUSDC"))
        p2 = MockPaire(Paire(binance.client, "SKLBTC"))
        p3 = MockPaire(Paire(binance.client, "BTCUSDC"))

        engine_order = OrderEngine(p1, p2, p3, 10)
        #order1 = engine_order.execute_trade_aller()
        #print(order1)

        order1 = engine_order.execute_trade_retour()
        print(order1)
