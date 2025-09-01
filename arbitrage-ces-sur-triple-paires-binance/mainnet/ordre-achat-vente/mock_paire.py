import time
import random
from decimal import Decimal
from paire import MinNotionalError, StepSizeError

class MockPaire:
    """
    Encapsule une vraie instance de Paire et simule les méthodes buy/sell
    en renvoyant un JSON proche de la réponse réelle Binance.
    """
    def __init__(self, vraie_paire):
        self._paire = vraie_paire

    def __getattr__(self, attr):
        return getattr(self._paire, attr)

    # -----------------------------
    # Méthodes simulées
    # -----------------------------
    def buy_base_from_quote(self, amount_quote: float) -> dict:
        prix = self._paire.prix
        step_size = self._paire.step_size
        min_notional = self._paire.min_notional
        base, quote = self._paire.assets()

        # Vérification minNotional
        if Decimal(amount_quote) < min_notional:
            message = f"Montant trop faible. MinNotional pour {self._paire.symbol} : {min_notional} {quote}"
            print("ERREUR:", message)
            raise MinNotionalError(message)

        # Calcul quantité de base à acheter
        qty_base = Decimal(amount_quote) / prix
        qty_base = (qty_base // step_size) * step_size
        qty_base = qty_base.quantize(Decimal("0.00000001"))

        # Générer JSON simulé
        order_id = random.randint(1000000000, 9999999999)
        transact_time = int(time.time() * 1000)

        fills = [
            {
                "price": f"{float(prix):.8f}",
                "qty": f"{float(qty_base):.8f}",
                "commission": f"{float(qty_base) * 0.001:.8f}",  # simulate 0.1% fee
                "commissionAsset": base,
                "tradeId": random.randint(1000000, 9999999)
            }
        ]

        return {
            "symbol": self._paire.symbol,
            "orderId": order_id,
            "orderListId": -1,
            "clientOrderId": f"x-{random.getrandbits(64):x}",
            "transactTime": transact_time,
            "price": "0.00000000",
            "origQty": f"{float(qty_base):.8f}",
            "executedQty": f"{float(qty_base):.8f}",
            "origQuoteOrderQty": "0.00000000",
            "cummulativeQuoteQty": f"{float(amount_quote):.8f}",
            "status": "FILLED",
            "timeInForce": "GTC",
            "type": "MARKET",
            "side": "BUY",
            "workingTime": transact_time,
            "fills": fills,
            "selfTradePreventionMode": "EXPIRE_MAKER"
        }

    def sell_base_get_quote(self, amount_base: float) -> dict:
        prix = self._paire.prix
        step_size = self._paire.step_size
        base, quote = self._paire.assets()

        if Decimal(amount_base) < step_size:
                message = f"Quantité trop faible. amount_base = {amount_base} {base}, stepSize = {step_size}"
                print("ERREUR:", message)
                raise StepSizeError(message)

        amount_base_dec = Decimal(amount_base).quantize(Decimal("0.00000001"))
        quote_qty = (amount_base_dec * prix).quantize(Decimal("0.00000001"))

        order_id = random.randint(1000000000, 9999999999)
        transact_time = int(time.time() * 1000)

        fills = [
            {
                "price": f"{float(prix):.8f}",
                "qty": f"{float(amount_base_dec):.8f}",
                "commission": f"{float(amount_base_dec) * 0.001:.8f}",
                "commissionAsset": base,
                "tradeId": random.randint(1000000, 9999999)
            }
        ]

        return {
            "symbol": self._paire.symbol,
            "orderId": order_id,
            "orderListId": -1,
            "clientOrderId": f"x-{random.getrandbits(64):x}",
            "transactTime": transact_time,
            "price": "0.00000000",
            "origQty": f"{float(amount_base_dec):.8f}",
            "executedQty": f"{float(amount_base_dec):.8f}",
            "origQuoteOrderQty": "0.00000000",
            "cummulativeQuoteQty": f"{float(quote_qty):.8f}",
            "status": "FILLED",
            "timeInForce": "GTC",
            "type": "MARKET",
            "side": "SELL",
            "workingTime": transact_time,
            "fills": fills,
            "selfTradePreventionMode": "EXPIRE_MAKER"
        }

# -----------------------------
# Exemple d'utilisation
# -----------------------------
if __name__ == "__main__":
    from paire import Paire
    from binance_client import BinanceClient

    with BinanceClient() as binance:
        vraie_paire = Paire(binance.client, "BTCUSDC")
        mock_paire = MockPaire(vraie_paire)

        print(mock_paire)
        achat = mock_paire.buy_base_from_quote(10)
        import json
        print("Achat simulé :", json.dumps(achat, indent=4))
        vente = mock_paire.sell_base_get_quote(0.00005)
        print("Vente simulée :", json.dumps(vente, indent=4))
