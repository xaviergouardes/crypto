from web3 import Web3
from web3.middleware import geth_poa_middleware

# --- Classe wrap / unwrap WBNB ---
class WBNBWrapper:
    # Adresse WBNB sur BSC Testnet
    WBNB_RAW = "0xae13d989dac2f0debff460ac112a837c89baa7cd"  # WBNB Testnet
    WBNB_ABI = [
        {
            "inputs": [],
            "name": "deposit",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "uint256","name": "wad","type": "uint256"}],
            "name": "withdraw",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    def __init__(self, web3: Web3, address_wallet: str):
        self.web3 = web3
        self.address = self.web3.to_checksum_address(address_wallet)
        self.wbnb = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.WBNB_RAW),
            abi=self.WBNB_ABI
        )

    def wrap(self, amount_bnb_wei: int):
        tx = self.wbnb.functions.deposit().build_transaction({
            "from": self.address,
            "value": amount_bnb_wei,
            "gas": 200000,
            "gasPrice": self.web3.to_wei('10', 'gwei'),
            "nonce": self.web3.eth.get_transaction_count(self.address)
        })
        return tx

    def unwrap(self, amount_wbnb_wei: int):
        tx = self.wbnb.functions.withdraw(amount_wbnb_wei).build_transaction({
            "from": self.address,
            "gas": 200000,
            "gasPrice": self.web3.to_wei('10', 'gwei'),
            "nonce": self.web3.eth.get_transaction_count(self.address)
        })
        return tx

# --- MAIN ---
if __name__ == "__main__":
    # Connexion BSC Testnet
    web3 = Web3(Web3.HTTPProvider("https://data-seed-prebsc-1-s1.binance.org:8545/"))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not web3.is_connected():
        print("❌ Impossible de se connecter au BSC Testnet")
        exit()

    wallet_address = "0x9e428f4042Be817983C2a810eDeA37CBa6aB940E"
    private_key = "72475f76b8527af9410651a1fc935745db94156b98f4c6bb2276b6a3a0937c0d"  # pour signer la transaction

    wrapper = WBNBWrapper(web3, wallet_address)

    # Exemple : wrap 1 BNB
    amount_to_wrap = web3.to_wei(1, 'ether')
    tx = wrapper.wrap(amount_to_wrap)

    # Signer et envoyer la transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"🚀 Transaction envoyée, hash: {web3.to_hex(tx_hash)}")
