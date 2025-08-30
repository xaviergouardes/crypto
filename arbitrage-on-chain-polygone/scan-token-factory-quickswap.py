from web3 import Web3

# Connexion Web3
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Vérification connexion
if not web3.is_connected():
    print("Erreur : impossible de se connecter à Polygon RPC")
    exit()

# Factory QuickSwap V2
FACTORY_ADDRESS = Web3.to_checksum_address("0x5757371414417b8c6caad45baef941abc7d3ab32")
FACTORY_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"name": "pair", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]
factory = web3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)

# Adresses tokens WETH et USDC Polygon (checksum)
USDC_ADDRESS = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
WETH_ADDRESS = Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619")

# Vérifier le pool WETH/USDC
pair_address = factory.functions.getPair(WETH_ADDRESS, USDC_ADDRESS).call()

if pair_address != "0x0000000000000000000000000000000000000000":
    print(f"Pool WETH/USDC trouvé : {pair_address}")
else:
    # Essayer l'ordre inverse USDC/WETH
    pair_address = factory.functions.getPair(USDC_ADDRESS, WETH_ADDRESS).call()
    if pair_address != "0x0000000000000000000000000000000000000000":
        print(f"Pool USDC/WETH trouvé : {pair_address}")
    else:
        print("Aucun pool WETH/USDC trouvé sur QuickSwap")
