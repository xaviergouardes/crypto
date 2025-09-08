from binance_client import BinanceClient
from decimal import Decimal
from paire import Paire
from mock_paire import MockPaire
import time
import json
from datetime import datetime
import logging


logger = logging.getLogger("order_engine")

class OrderEngine:
    def __init__(self, usdc1: Paire, inter: Paire, usdc2: Paire, capital: Decimal = Decimal("100")):
         self.usdc1 = usdc1
         self.inter = inter
         self.usdc2 = usdc2
         self.capital = capital


    def execute_trade_aller(self):
            # USDC -> Intermédiaire
            try:
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"execute_trade_aller - order1 = buy_base_from_quote(capital={self.capital})")
                order1 = self.usdc1.buy_base_from_quote(self.capital)
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"Binance - execute_trade_aller - order1 ={order1})")
                qty_base1 = Decimal(order1["executedQty"])

            except Exception as e:
                logger.error(f"Erreur dans execute_trade_aller.buy_base_from_quote : order1 - exception={e}")
                logger.error(f"Erreur dans execute_trade_aller.buy_base_from_quote({self.capital})")
                raise e

            # Intermédiaire -> Autre crypto
            try:
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"execute_trade_aller - order2 = sell_base_get_quote(qty_base1={qty_base1})")
                order2 = self.inter.sell_base_get_quote(qty_base1)
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"Binance - execute_trade_aller - order2 ={order2})")
                qty_base2 = Decimal(order2["cummulativeQuoteQty"])

            except Exception as e:
                logger.error(f"Erreur dans execute_trade_aller.sell_base_get_quote : order2 - exception={e}")
                logger.error(f"Erreur dans execute_trade_aller.sell_base_get_quote : order1={order1}")
                logger.error(f"Erreur dans execute_trade_aller.sell_base_get_quote({qty_base1})")

                raise e

            # Autre crypto -> USDC
            try:
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"execute_trade_aller - order3 = sell_base_get_quote(qty_base2={qty_base2})")
                order3 = self.usdc2.sell_base_get_quote(qty_base2)
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"Binance - execute_trade_aller - order3 ={order3})")
                #final_usdc = Decimal(order3["cummulativeQuoteQty"])


            except Exception as e:
                logger.error(f"Erreur dans execute_trade_aller.sell_base_get_quote : order3 - exception={e}")
                logger.error(f"Erreur dans execute_trade_aller.sell_base_get_quote : order1={order1}")
                logger.error(f"Erreur dans execute_trade_aller.sell_base_get_quote : order2={order2}")
                logger.error(f"Erreur dans execute_trade_aller.sell_base_get_quote({qty_base2})")
                raise e
            
            #print(f"[TRADE ALLER] Capital initial={self.capital}, Capital final={final_usdc:.8f}")

            return [order1, order2, order3]

    def execute_trade_retour(self):

            # USDC -> Autre crypto (BTC par ex.)
            try:
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"execute_trade_retour - order1 = buy_base_from_quote(capital={self.capital})")
                order1 = self.usdc2.buy_base_from_quote(self.capital)
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"Binance - execute_trade_retour - order1 ={order1})")
                qty_base1 = Decimal(order1["executedQty"])

            except Exception as e:
                logger.error(f"Erreur dans execute_trade_retour.buy_base_from_quote : order1 - exception={e}")
                logger.error(f"Erreur dans execute_trade_retour.buy_base_from_quote({self.capital})")
                raise e

            # Autre crypto -> Intermédiaire (ETH par ex.)
            try:
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"execute_trade_retour - order2 = buy_base_from_quote(qty_base1={qty_base1})")
                order2 = self.inter.buy_base_from_quote(float(qty_base1))
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"Binance - execute_trade_retour - order2 ={order2})")
                qty_base2 = Decimal(order2["executedQty"])

            except Exception as e:
                logger.error(f"Erreur dans execute_trade_retour.buy_base_from_quote : order2 - exception={e}")
                logger.error(f"Erreur dans execute_trade_retour.buy_base_from_quote : order1={order1}")
                logger.error(f"Erreur dans execute_trade_retour.buy_base_from_quote({self.capital})")
                raise e
    
            # Intermédiaire -> USDC
            try:
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"execute_trade_retour - order3 = sell_base_get_quote(qty_base2={qty_base2})")
                order3 = self.usdc1.sell_base_get_quote(qty_base2)
                #if logger.isEnabledFor(logging.DEBUG): logger.debug(f"Binance - execute_trade_retour - order3 ={order3})")
                #final_usdc = Decimal(order3["cummulativeQuoteQty"])

            except Exception as e:
                logger.error(f"Erreur dans execute_trade_retour.sell_base_get_quote : order3 - exception={e}")
                logger.error(f"Erreur dans execute_trade_retour.sell_base_get_quote : order1={order1}")
                logger.error(f"Erreur dans execute_trade_retour.sell_base_get_quote : order2={order2}")
                logger.error(f"Erreur dans execute_trade_retour.sell_base_get_quote({self.capital})")
                raise e

            return [order1, order2, order3]


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
        order1 = engine_order.execute_trade_aller()
        print(order1)

        order1 = engine_order.execute_trade_retour()
        print(order1)
