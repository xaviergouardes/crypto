from web3 import Web3

# --- Configuration ---
INFURA_URL = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"  # Remplace par ton endpoint
POOL_ADDRESS = Web3.to_checksum_address("0x6418eec70f50913ff0d756b48d32ce7c02b47c47")  # USDC/WETH Sepolia

# Connexion Web3
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ABI minimale pour lire token0, token1, liquidity et slot0
POOL_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "liquidity", "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "slot0", "outputs": [
        {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
        {"internalType": "int24", "name": "tick", "type": "int24"},
        {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
        {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
        {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
        {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
        {"internalType": "bool", "name": "unlocked", "type": "bool"}
    ], "stateMutability": "view", "type": "function"}
]

pool = w3.eth.contract(address=POOL_ADDRESS, abi=POOL_ABI)

# --- Vérifier la liquidité ---
liquidity = pool.functions.liquidity().call()
if liquidity == 0:
    print("Le pool n'est pas actif (liquidité = 0).")
    exit()
else:
    print(f"Le pool est actif (liquidité = {liquidity}).")

# --- Récupérer les adresses des tokens ---
token0_address = pool.functions.token0().call()
token1_address = pool.functions.token1().call()

# Symboles connus pour Sepolia USDC/WETH
token_symbols = {
    Web3.to_checksum_address("0x1c7d4b196cb0c7b01d743fbc6116a902379c7238"): "USDC",
    Web3.to_checksum_address("0xfff9976782d46cc05630d1f6ebab18b2324d6b14"): "WETH"
}

token0_symbol = token_symbols.get(token0_address, "TOKEN0")
token1_symbol = token_symbols.get(token1_address, "TOKEN1")

# --- Récupérer slot0 ---
slot0 = pool.functions.slot0().call()
sqrtPriceX96 = slot0[0]

# --- Calculer le prix correctement ---
# sqrtPriceX96 = sqrt(token1/token0) * 2^96
price_token1_per_token0 = (sqrtPriceX96 / 2**96) ** 2   # token1/token0
price_token0_per_token1 = 1 / price_token1_per_token0   # token0/token1

# --- Affichage réaliste ---
if token0_symbol == "USDC" and token1_symbol == "WETH":
    print(f"1 {token0_symbol} = {price_token1_per_token0:.20f} {token1_symbol}")
    print(f"1 {token1_symbol} = {price_token0_per_token1:.20f} {token0_symbol}")
else:
    # Si ordre inverse
    print(f"1 WETH = {price_token0_per_token1:.20f} USDC")
    print(f"1 USDC = {price_token1_per_token0:.20f} WETH")
