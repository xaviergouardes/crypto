from binance.client import Client
from decimal import Decimal

class Paire:
    """
    Représente une paire de trading Binance.
    Fournit le prix actuel, le minNotional et le symbole.
    """
    def __init__(self, binance_client: Client, symbol: str):
        self.client = binance_client
        self.symbol = symbol.upper()
        self.info = self.client.get_symbol_info(self.symbol)
        
        if not self.info:
            raise ValueError(f"Impossible de trouver la paire {self.symbol}")

    @property
    def prix(self) -> float:
        """Retourne le prix actuel de la paire."""
        ticker = self.client.get_symbol_ticker(symbol=self.symbol)
        return Decimal(ticker["price"])

    @property
    def min_notional(self) -> float:
        """Retourne le montant minimal (NOTIONAL) obligatoire pour un ordre."""
        for f in self.info["filters"]:
            if f["filterType"] == "NOTIONAL":
                return Decimal(f["minNotional"])
        return None

    @property
    def step_size(self) -> float:
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
    
    def __str__(self) -> str:
        """Retourne une représentation lisible de la paire."""
        base, quote = paire.assets()
        return (
            f"{self.symbol} | Prix: {self.prix} | MinNotional: {self.min_notional} {quote} | "
            f"StepSize: {self.step_size} {base}"
        )

# Exemple d’utilisation
if __name__ == "__main__":
    from binance_client import BinanceClient   # ta classe précédente
    
    with BinanceClient() as binance:
        paire = Paire(binance.client, "BTCUSDC")
        print(paire)   # <-- appelle __str__()  

