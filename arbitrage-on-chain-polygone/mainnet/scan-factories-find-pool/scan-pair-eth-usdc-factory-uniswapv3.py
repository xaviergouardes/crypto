from web3 import Web3

# Connexion Web3 Polygon
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("Erreur : impossible de se connecter à Polygon RPC")
    exit()

# Factory Uniswap V3 Polygon
FACTORY_ADDRESS = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address","name": "tokenA","type": "address"},
            {"internalType": "address","name": "tokenB","type": "address"},
            {"internalType": "uint24","name": "fee","type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address","name": "pool","type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

factory = web3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)

# Adresses WETH et USDC Polygon
USDC_ADDRESS = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
WETH_ADDRESS = Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619")

# Les pools Uniswap V3 ont des frais fixes, généralement 500, 3000, 10000 (0.05%, 0.3%, 1%)
fees = [500, 3000, 10000]

found = False
for fee in fees:
    pair_address = factory.functions.getPool(WETH_ADDRESS, USDC_ADDRESS, fee).call()
    if pair_address != "0x0000000000000000000000000000000000000000":
        print(f"Pool WETH/USDC trouvé sur Uniswap V3 Polygon avec fee {fee} : {pair_address}")
        found = True
    else:
        pair_address = factory.functions.getPool(USDC_ADDRESS, WETH_ADDRESS, fee).call()
        if pair_address != "0x0000000000000000000000000000000000000000":
            print(f"Pool USDC/WETH trouvé sur Uniswap V3 Polygon avec fee {fee} : {pair_address}")
            found = True

if not found:
    print("Aucun pool WETH/USDC trouvé sur Uniswap V3 Polygon")
