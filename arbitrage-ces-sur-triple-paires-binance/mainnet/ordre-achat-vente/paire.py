from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from decimal import Decimal
import time
from binance_client import BinanceClient   # ta classe précédente

class MinNotionalError(Exception):
    """Exception levée lorsque le montant en quote est inférieur au minNotional."""
    pass

class StepSizeError(Exception):
    """Exception levée lorsque la quantité est inférieure au step_size."""
    pass

class Paire:
    """
    Représente une paire de trading Binance.
    Fournit le prix actuel, le minNotional et le symbole.
    """
    def __init__(self, binance_client: Client, symbol: str):
        self.client = binance_client
        self.symbol = symbol.upper()
        self.info = self.client.get_symbol_info(self.symbol)
        ticker = self.client.get_symbol_ticker(symbol=self.symbol) 
        self._dernier_prix = Decimal(ticker["price"])
        
        if not self.info:
            raise ValueError(f"Impossible de trouver la paire {symbol}")

    @property
    def prix(self) -> Decimal:
        """Retourne le prix actuel de la paire."""
        #ticker = await asyncio.to_thread(
        #    self.client.get_symbol_ticker(symbol=self.symbol)
        #)
        ticker = self.client.get_symbol_ticker(symbol=self.symbol)
        self._dernier_prix = Decimal(ticker["price"])
        return self._dernier_prix

    @property
    def min_notional(self) -> Decimal:
        """Retourne le montant minimal (NOTIONAL) obligatoire pour un ordre."""
        for f in self.info["filters"]:
            if f["filterType"] == "NOTIONAL":
                return Decimal(f["minNotional"])
        return None

    @property
    def step_size(self) -> Decimal:
        """Retourne la taille minimale de lot (quantité minimale)."""
        for f in self.info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                return Decimal(f["stepSize"])
        return None

    def symbol_pair(self) -> str:
        """Retourne le symbole de la paire (ex: BTCUSDC)."""
        return self.symbol
    
    def assets(self) -> tuple[str, str]:
        """Retourne les deux actifs qui composent la paire (base, quote)."""
        return (self.info["baseAsset"], self.info["quoteAsset"])

    def buy_base_from_quote(self, amount_quote: Decimal) -> dict:
        """
        Acheter la paire avec un ordre MARKET à partir d'un montant en quote asset.
        Renvoie toutes les données de la transaction.
        :param amount_quote: Montant en quote asset à utiliser.
        :return: dictionnaire contenant les informations de l'ordre.
        """
        min_notional = self.min_notional
        if min_notional is not None and Decimal(amount_quote) < min_notional:
            message = f"Montant trop faible. MinNotional pour {self.symbol} : {min_notional} {self.quote_asset()}"
            print(message)
            raise MinNotionalError(message)
        
        try:
            order = self.client.order_market_buy(
                symbol=self.symbol,
                quoteOrderQty=amount_quote
            )
            return order
        
        except (BinanceAPIException, BinanceOrderException) as e:
            print(f"Erreur lors de l'achat MARKET: {e}")
            return None
        
    def sell_base_get_quote(self, amount_base: Decimal) -> dict:
        """
        Vendre une quantité de base asset pour récupérer des quote via un ordre MARKET.
        :param amount_base: quantité de base à vendre
        :return: dictionnaire contenant les informations de l'ordre
        """
        # Vérifier step_size
        if amount_base < self.step_size:
            msg = (f"Quantité trop faible. amount_base = {amount_base} {self.base_asset}, "
                   f"stepSize = {self.step_size}")
            print("ERREUR:", msg)
            raise StepSizeError(msg)

        try:
            order = self.client.order_market_sell(
                symbol=self.symbol,
                quantity=amount_base
            )
            print(f"Vente réussie : {amount_base} {self.base_asset}")
            return order

        except (BinanceAPIException, BinanceOrderException) as e:
            print(f"Erreur lors de la vente MARKET: {e}")
            return None
        

    def __str__(self) -> str:
        """Retourne une représentation lisible de la paire."""
        base, quote = paire.assets()
        return (
            f"{self.symbol} | Prix: {self._dernier_prix:.8f} | "
            f"MinNotional: {self.min_notional:.8f} {quote} | "
            f"StepSize: {self.step_size:.8f} {base}"
        )


if __name__ == "__main__":
    # ['SKLUSDC', 'SKLBTC', 'BTCUSDC'] 
    with BinanceClient() as binance:
        paire = Paire(binance.client, "SKLUSDC")
        print(paire)   # <-- appelle __str__()  
        print(paire.prix)

        paire = Paire(binance.client, "SKLBTC")
        print(paire)   
        print(paire.prix)

        paire = Paire(binance.client, "BTCUSDC")
        print(paire)   
        print(paire.prix)