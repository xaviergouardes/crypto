import time
from web3 import Web3

# Connexion Web3 Polygon
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("Erreur : impossible de se connecter à Polygon RPC")
    exit()

# Pools WETH/USDC (checksum)
UNISWAP_POOL = Web3.to_checksum_address("0x45dDa9cb7c25131DF268515131f647d726f50608")
QUICKSWAP_POOL = Web3.to_checksum_address("0x5757371414417b8c6caad45baef941abc7d3ab32")

SWAP_FEE = 0.003  # 0,3% frais typique

# ABI minimale pour QuickSwap V2
QUICKSWAP_ABI = [
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
    }
]

# ABI minimale pour Uniswap V3
UNISWAP_V3_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_price_quickswap(pool_address):
    pool = web3.eth.contract(address=pool_address, abi=QUICKSWAP_ABI)
    reserve_weth, reserve_usdc, _ = pool.functions.getReserves().call()
    price = reserve_usdc / reserve_weth
    return price, reserve_weth, reserve_usdc

def get_price_uniswap_v3(pool_address):
    pool = web3.eth.contract(address=pool_address, abi=UNISWAP_V3_ABI)
    sqrtPriceX96 = pool.functions.slot0().call()[0]
    price = (sqrtPriceX96 / 2**96) ** 2  # USDC/WETH
    return price

def main():
    while True:
        try:
            price_uni = get_price_uniswap_v3(UNISWAP_POOL)
            price_quick, liq_weth_quick, liq_usdc_quick = get_price_quickswap(QUICKSWAP_POOL)
            
            print(f"Prix Uniswap V3 WETH/USDC : {price_uni:.6f}")
            print(f"Prix QuickSwap WETH/USDC : {price_quick:.6f} | Liquidité WETH : {liq_weth_quick}")
            
            # Ajustement prix pour frais
            adjusted_price_uni = price_uni * (1 + SWAP_FEE)
            adjusted_price_quick = price_quick * (1 + SWAP_FEE)
            
            # Détection arbitrage
            if adjusted_price_uni < price_quick:
                max_trade_weth = liq_weth_quick * 0.1
                print(f"🚀 Arbitrage potentiel : Acheter WETH sur Uniswap, vendre sur QuickSwap | Max WETH tradeable : {max_trade_weth:.4f}")
            elif adjusted_price_quick < price_uni:
                max_trade_weth = liq_weth_quick * 0.1
                print(f"🚀 Arbitrage potentiel : Acheter WETH sur QuickSwap, vendre sur Uniswap | Max WETH tradeable : {max_trade_weth:.4f}")
            else:
                print("✅ Pas d'opportunité profitable actuellement")
            
            print("-" * 60)
            time.sleep(5)
        except Exception as e:
            print("Erreur :", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
