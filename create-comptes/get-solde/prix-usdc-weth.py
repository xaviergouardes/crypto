from web3 import Web3

INFURA_URL = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"

# Convertir en adresse checksum
POOL_ADDRESS = Web3.to_checksum_address("0x3289680dd4d6c10bb19b899729cda5eef58aeff1")
TOKEN0_SYMBOL = "USDC"
TOKEN1_SYMBOL = "WETH"

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

POOL_ABI = [
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

liquidity = pool.functions.liquidity().call()
if liquidity == 0:
    print("Le pool n'est pas actif (liquidité = 0).")
else:
    print(f"Le pool est actif (liquidité = {liquidity}).")
    slot0 = pool.functions.slot0().call()
    sqrtPriceX96 = slot0[0]
    price = (sqrtPriceX96 ** 2) / (2 ** 192)
    print(f"Prix actuel : 1 {TOKEN0_SYMBOL} = {price:.6f} {TOKEN1_SYMBOL}")
    print(f"Prix actuel : 1 {TOKEN1_SYMBOL} = {1/price:.6f} {TOKEN0_SYMBOL}")
