import time
from decimal import Decimal, getcontext
from web3 import Web3

# Augmenter la précision pour manipuler de grands nombres
getcontext().prec = 50

class QuickSwapPool:
    # Variables intégrées à la classe
    RPC_URL = "https://polygon-rpc.com"
    QUICKSWAP_POOL = "0x853Ee4b2A13f8a742d64C8F088bE7bA2131f670d"
    WETH_ADDRESS = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
    USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

    # Décimales des tokens
    DECIMALS = {
        "WETH": 18,
        "USDC": 6
    }

    # ABI minimale pour lire les réserves et les tokens
    POOL_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    ]

    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        if not self.web3.is_connected():
            raise ConnectionError("Impossible de se connecter à Polygon RPC")

        self.pool_address = Web3.to_checksum_address(self.QUICKSWAP_POOL)
        self.weth_address = Web3.to_checksum_address(self.WETH_ADDRESS)
        self.usdc_address = Web3.to_checksum_address(self.USDC_ADDRESS)

        # Contrat pool
        self.pool = self.web3.eth.contract(address=self.pool_address, abi=self.POOL_ABI)

        # Tokens du pool
        self.token0 = self.pool.functions.token0().call()
        self.token1 = self.pool.functions.token1().call()

        # Déterminer l’ordre pour WETH/USDC
        self.invert_price = (self.token0.lower() == self.usdc_address.lower())

    def get_reserves(self):
        """Récupère les réserves du pool"""
        reserve0, reserve1, _ = self.pool.functions.getReserves().call()
        # Ajuster les décimales
        if self.token0.lower() == self.usdc_address.lower():
            reserve_usdc = Decimal(reserve0) / (10 ** self.DECIMALS["USDC"])
            reserve_weth = Decimal(reserve1) / (10 ** self.DECIMALS["WETH"])
        else:
            reserve_usdc = Decimal(reserve1) / (10 ** self.DECIMALS["USDC"])
            reserve_weth = Decimal(reserve0) / (10 ** self.DECIMALS["WETH"])
        return reserve_weth, reserve_usdc

    def get_price(self):
        """Calcule le prix WETH/USDC"""
        reserve_weth, reserve_usdc = self.get_reserves()
        if reserve_weth == 0:
            return Decimal(0)
        return reserve_usdc / reserve_weth

def main():
    pool = QuickSwapPool()
    print(f"Token0 : {pool.token0} | Token1 : {pool.token1}")
    while True:
        try:
            price = pool.get_price()
            reserve_weth, reserve_usdc = pool.get_reserves()
            print(f"Prix WETH/USDC QuickSwap : {price:.2f} | Réserves WETH : {reserve_weth:.4f} | Réserves USDC : {reserve_usdc:.2f}")
            time.sleep(10)
        except Exception as e:
            print("Erreur :", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
