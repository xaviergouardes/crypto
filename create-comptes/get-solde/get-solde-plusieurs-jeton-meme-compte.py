from web3 import Web3

# -----------------------
# CONFIG
# -----------------------
INFURA_URL = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"
ADDRESS = "0x65390B0bb9420BD83b1325Bf05dF1b4A8b2938B4"

# Contrats ERC-20 sur Sepolia
TOKENS = {
    "USDC": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    "EURC": "0x08210F9170F89Ab7658F0B5E3fF39b0E03C594D4"
}

# ABI minimale pour lecture ERC20
ERC20_ABI = [
    {"constant": True,"inputs": [],"name": "decimals","outputs": [{"name": "","type": "uint8"}],"type": "function"},
    {"constant": True,"inputs": [{"name": "_owner","type": "address"}],"name": "balanceOf","outputs": [{"name": "balance","type": "uint256"}],"type": "function"},
    {"constant": True,"inputs": [],"name": "symbol","outputs": [{"name": "","type": "string"}],"type": "function"}
]

# -----------------------
# SCRIPT
# -----------------------
def main():
    w3 = Web3(Web3.HTTPProvider(INFURA_URL))
    if not w3.is_connected():
        print("❌ Connexion échouée")
        return

    # Solde ETH natif
    eth_balance = w3.eth.get_balance(ADDRESS)
    print(f"ETH balance: {w3.from_wei(eth_balance, 'ether')} ETH")

    # Soldes ERC20
    for name, contract_addr in TOKENS.items():
        token = w3.eth.contract(address=contract_addr, abi=ERC20_ABI)
        decimals = token.functions.decimals().call()
        balance = token.functions.balanceOf(ADDRESS).call() / (10 ** decimals)
        symbol = token.functions.symbol().call()
        print(f"{name} balance: {balance} {symbol}")

if __name__ == "__main__":
    main()
