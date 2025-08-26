from web3 import Web3

class PancakeSwapPrice:
    # Adresses tokens BSC
    WBNB_RAW = "0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
    WUSDC_RAW = "0x8AC76a51cc950d9822D68b83fe1Ad97B32Cd580d"
    ROUTER_RAW = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

    def __init__(self, bsc_rpc="https://bsc-dataseed.binance.org/"):
        self.web3 = Web3(Web3.HTTPProvider(bsc_rpc))
        if not self.web3.is_connected():
            raise Exception("Impossible de se connecter à BSC")

        # Convertir en adresses checksummed
        self.WBNB = self.web3.to_checksum_address(self.WBNB_RAW)
        self.WUSDC = self.web3.to_checksum_address(self.WUSDC_RAW)
        router_address = self.web3.to_checksum_address(self.ROUTER_RAW)

        # ABI minimal pour getAmountsOut
        router_abi = [
            {
                "inputs": [
                    {"internalType": "uint256","name": "amountIn","type": "uint256"},
                    {"internalType": "address[]","name": "path","type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]","name": "amounts","type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

        self.router = self.web3.eth.contract(address=router_address, abi=router_abi)

    def get_price(self, amount_in_wei=10**18):
        """Récupère le prix WBNB -> WUSDC pour amount_in_wei WBNB"""
        path = [self.WBNB, self.WUSDC]
        amounts = self.router.functions.getAmountsOut(amount_in_wei, path).call()
        price_wbnb_usdc = amounts[1] / 1e18  # WUSDC a 18 décimales
        return price_wbnb_usdc


# --- Main qui boucle toutes les 10 secondes ---
if __name__ == "__main__":
    import time
    ps = PancakeSwapPrice()
    print("🚀 Surveillance des prix WBNB/WUSDC sur PancakeSwap...")

    while True:
        try:
            price = ps.get_price()
            print(f"💧 Prix live WBNB/WUSDC: {price:.2f} USDC")
            time.sleep(10)
        except Exception as e:
            print("Erreur:", e)
            time.sleep(10)
