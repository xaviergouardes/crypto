from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance_client import BinanceClient

class BinanceTrader:
    """
    Classe qui permet de passer des ordres d'achat/vente sur Binance Spot
    en utilisant un BinanceClient.
    """
    def __init__(self, client: BinanceClient):
        self.client = client

    def buy(self, symbol, quantity, price=None, order_type="MARKET"):
        try:
            binance_client = self.client.client
            if order_type == "MARKET":
                return binance_client.order_market_buy(symbol=symbol, quantity=quantity)
            elif order_type == "LIMIT":
                if price is None:
                    raise ValueError("Le prix doit être précisé pour un ordre LIMIT.")
                return binance_client.order_limit_buy(symbol=symbol, quantity=quantity, price=str(price))
            else:
                raise ValueError("Type d'ordre non supporté.")
        except (BinanceAPIException, BinanceOrderException) as e:
            print(f"Erreur lors de l'achat: {e}")
            return None

    def sell(self, symbol, quantity, price=None, order_type="MARKET"):
        try:
            binance_client = self.client.client
            if order_type == "MARKET":
                return binance_client.order_market_sell(symbol=symbol, quantity=quantity)
            elif order_type == "LIMIT":
                if price is None:
                    raise ValueError("Le prix doit être précisé pour un ordre LIMIT.")
                return binance_client.order_limit_sell(symbol=symbol, quantity=quantity, price=str(price))
            else:
                raise ValueError("Type d'ordre non supporté.")
        except (BinanceAPIException, BinanceOrderException) as e:
            print(f"Erreur lors de la vente: {e}")
            return None

# Exemple d'utilisation
if __name__ == "__main__":

    from binance_client import BinanceClient

    with BinanceClient() as client:
        trader = BinanceTrader(client=client)

        # Achat market
        result = trader.buy("BTCUSDC", quantity="0.00005")
        print(result)

        # Vente limit
        result = trader.sell("BTCUSDT", quantity=0.001, price=50000, order_type="LIMIT")
        print(result)