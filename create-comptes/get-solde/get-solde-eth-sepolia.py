from web3 import Web3

# URL RPC Sepolia (ici Infura, tu dois remplacer YOUR_INFURA_API_KEY par ta clé)
RPC_URL = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"

# Connexion au réseau
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Vérifier la connexion
if not web3.is_connected():
    print("❌ Impossible de se connecter à Sepolia, vérifie ton RPC_URL")
    exit()

# Adresse Ethereum à vérifier
address = "0x65390B0bb9420BD83b1325Bf05dF1b4A8b2938B4"

# Récupérer le solde (en wei)
balance_wei = web3.eth.get_balance(address)

# Conversion en ETH
balance_eth = web3.from_wei(balance_wei, "ether")

print(f"Solde de {address} : {balance_eth} ETH (Sepolia)")
