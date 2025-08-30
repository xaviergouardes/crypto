from web3 import Web3

# Connexion au RPC HyperEVM Testnet
RPC_URL = "https://rpc.hyperliquid-testnet.xyz/evm"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    print("❌ Échec de connexion")
    exit()
print("✅ Connecté au testnet HyperEVM")

# Adresse brute du pool HYPE/USDC (à remplacer par l'adresse réelle)
POOL_ADDRESS_RAW = "0xb9f2e2b5af029e9ad090269dad41c4df"

# Conversion en checksum address
POOL_ADDRESS = w3.to_checksum_address(POOL_ADDRESS_RAW)

# ABI minimale pour lire le pool
PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
]

# Création du contrat
pair_contract = w3.eth.contract(address=POOL_ADDRESS, abi=PAIR_ABI)

# Lecture des réserves
reserves = pair_contract.functions.getReserves().call()
token0 = pair_contract.functions.token0().call()
token1 = pair_contract.functions.token1().call()

print(f"Token0 : {token0}, Token1 : {token1}")
print(f"Réserves : {reserves}")

# Exemple simple de calcul de prix
price = reserves[1] / reserves[0]
print(f"Prix approximatif HYPE/USDC : {price}")
