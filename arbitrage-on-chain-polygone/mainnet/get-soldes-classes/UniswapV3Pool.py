import time
from decimal import Decimal, getcontext
from web3 import Web3

# Augmenter la précision pour manipuler de grands nombres
getcontext().prec = 50

class UniswapV3Pool:
    # Variables intégrées à la classe
    RPC_URL = "https://polygon-rpc.com"
    UNISWAP_POOL = "0x45dDa9cb7c25131DF268515131f647d726f50608"
    WETH_ADDRESS = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
    USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

    # Décimales des tokens
    DECIMALS = {
        "WETH": 18,
        "USDC": 6
    }

    # ABI minimale ERC20 pour récupérer le symbole
    ERC20_ABI = [
        {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    ]

    def __init__(self):
        # Connexion Web3
        self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        if not self.web3.is_connected():
            raise ConnectionError("Impossible de se connecter à la blockchain")

        # Adresses pool et tokens
        self.pool_address = Web3.to_checksum_address(self.UNISWAP_POOL)
        self.weth_address = Web3.to_checksum_address(self.WETH_ADDRESS)
        self.usdc_address = Web3.to_checksum_address(self.USDC_ADDRESS)

        # ABI minimale pour slot0, token0 et token1
        self.pool = self.web3.eth.contract(
            address=self.pool_address,
            abi=[
                {"inputs": [], "name": "slot0", "outputs": [
                    {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
                    {"internalType": "int24", "name": "tick", "type": "int24"},
                    {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
                    {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
                    {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
                    {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
                    {"internalType": "bool", "name": "unlocked", "type": "bool"}
                ], "stateMutability": "view", "type": "function"},
                {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
                {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
            ]
        )

        # Récupérer les tokens du pool
        self.token0 = self.pool.functions.token0().call()
        self.token1 = self.pool.functions.token1().call()

        # Symboles des tokens
        self.token0_symbol = self.web3.eth.contract(address=self.token0, abi=self.ERC20_ABI).functions.symbol().call()
        self.token1_symbol = self.web3.eth.contract(address=self.token1, abi=self.ERC20_ABI).functions.symbol().call()

        # Déterminer si le pool est inversé pour afficher WETH/USDC
        self.invert_price = (self.token0.lower() == self.usdc_address.lower())

    def get_price(self):
        """Retourne le prix WETH/USDC du pool avec Decimal pour précision"""
        sqrtPriceX96 = Decimal(self.pool.functions.slot0().call()[0])
        price = (sqrtPriceX96 ** 2) / Decimal(2 ** 192)

        # Ajuster pour décimales
        if self.invert_price:
            # token0 = USDC → inverser pour WETH/USDC
            price = Decimal(1) / price
            price *= Decimal(10 ** (self.DECIMALS["WETH"] - self.DECIMALS["USDC"]))
        else:
            # token0 = WETH → prix WETH/USDC
            price *= Decimal(10 ** (self.DECIMALS["WETH"] - self.DECIMALS["USDC"]))

        return price

def main():
    pool = UniswapV3Pool()
    print(f"Token0 : {pool.token0_symbol} | Token1 : {pool.token1_symbol}")
    while True:
        try:
            price = pool.get_price()
            print(f"Prix WETH/USDC : {price:.2f}")
            time.sleep(10)
        except Exception as e:
            print("Erreur :", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
