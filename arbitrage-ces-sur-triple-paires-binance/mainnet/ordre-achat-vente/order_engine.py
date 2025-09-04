from binance_client import BinanceClient
from decimal import Decimal
from paire import Paire
from mock_paire import MockPaire

class OrderEngine:
    def __init__(self, usdc1: Paire, inter: Paire, usdc2: Paire, capital: Decimal = Decimal("100")):
         self.usdc1 = usdc1
         self.inter = inter
         self.usdc2 = usdc2
         self.capital = capital

    def execute_trade_aller(self):
            # USDC -> Intermédiaire
            order1 = self.usdc1.buy_base_from_quote(self.capital)
            qty_base1 = Decimal(order1["executedQty"])

            # Intermédiaire -> Autre crypto
            order2 = self.inter.sell_base_get_quote(qty_base1)
            qty_base2 = Decimal(order2["cummulativeQuoteQty"])

            # Autre crypto -> USDC
            order3 = self.usdc2.sell_base_get_quote(qty_base2)
            final_usdc = Decimal(order3["cummulativeQuoteQty"])

            #print(f"[TRADE ALLER] Capital initial={self.capital}, Capital final={final_usdc:.8f}")

            return [order1, order2, order3]

    def execute_trade_retour(self):

            # USDC -> Autre crypto (BTC par ex.)
            order1 = self.usdc2.buy_base_from_quote(self.capital)
            qty_base1 = Decimal(order1["executedQty"])

            # Autre crypto -> Intermédiaire (ETH par ex.)
            order2 = self.inter.buy_base_from_quote(float(qty_base1))
            qty_base2 = Decimal(order2["executedQty"])

            # Intermédiaire -> USDC
            order3 = self.usdc1.sell_base_get_quote(qty_base2)
            final_usdc = Decimal(order3["cummulativeQuoteQty"])

            #print(f"[TRADE RETOUR] Capital initial={self.capital}, Capital final={final_usdc:.8f}")

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

        engine_order = OrderEngine(p1, p2, p3, 100)
        #order1 = engine_order.execute_trade_aller()
        #print(order1)

        order1 = engine_order.execute_trade_retour()
        print(order1)
