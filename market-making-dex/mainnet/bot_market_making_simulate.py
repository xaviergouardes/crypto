import json
import time
from web3 import Web3

# 🔹 Connexion Mainnet via Infura
MAINNET_RPC = "https://mainnet.infura.io/v3/3bdc55739dab4115ad4b202733a69938"
w3 = Web3(Web3.HTTPProvider(MAINNET_RPC))
if not w3.is_connected():
    raise Exception("❌ Connexion Mainnet échouée")
print("✅ Connexion Mainnet :", w3.is_connected())

# 🔹 Router Uniswap V2
ROUTER_ADDRESS = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
router_abi = json.loads("""
[{"inputs": [], "name": "factory", "outputs": [{"internalType": "address","name": "","type": "address"}],
  "stateMutability": "view","type": "function"}]
""")
router = w3.eth.contract(address=ROUTER_ADDRESS, abi=router_abi)

# 🔹 Factory Uniswap V2
FACTORY_ADDRESS = router.functions.factory().call()
factory_abi = json.loads("""
[
  {"constant": true,"inputs": [],"name": "allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
   "stateMutability": "view","type": "function"},
  {"constant": true,"inputs":[{"internalType": "uint256","name":"","type":"uint256"}],
   "name": "allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],
   "stateMutability": "view","type": "function"}
]
""")
factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)

print(f"Router : {ROUTER_ADDRESS}")
print(f"Factory : {FACTORY_ADDRESS}\n")

# 🔹 Paire fixe WETH/USDC (Mainnet)
PAIR_ADDRESS = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"

pair_abi = json.loads("""
[
  {"constant": true,"inputs": [],"name": "token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability": "view","type": "function"},
  {"constant": true,"inputs": [],"name": "token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability": "view","type": "function"},
  {"constant": true,"inputs": [],"name": "getReserves",
   "outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},
              {"internalType":"uint112","name":"_reserve1","type":"uint112"},
              {"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],
   "stateMutability": "view","type": "function"}
]
""")

erc20_abi = json.loads("""
[
  {"constant": true,"inputs": [],"name": "symbol","outputs":[{"name":"","type":"string"}],"stateMutability": "view","type": "function"},
  {"constant": true,"inputs": [],"name": "decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability": "view","type": "function"}
]
""")

# 🔹 Création du contrat pair
pair_contract = w3.eth.contract(address=PAIR_ADDRESS, abi=pair_abi)
token0_addr = pair_contract.functions.token0().call()
token1_addr = pair_contract.functions.token1().call()

token0_contract = w3.eth.contract(address=token0_addr, abi=erc20_abi)
token1_contract = w3.eth.contract(address=token1_addr, abi=erc20_abi)

symbol0 = token0_contract.functions.symbol().call()
symbol1 = token1_contract.functions.symbol().call()
decimals0 = token0_contract.functions.decimals().call()
decimals1 = token1_contract.functions.decimals().call()

print(f"Paire : {PAIR_ADDRESS} ({symbol0}/{symbol1})")

# 🔹 Paramètres paper trading
BASE_AMOUNT_WETH = 0.01
SPREAD = 0.005

def get_price():
    reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
    if symbol0.upper() == "WETH":
        return (reserve1 / 10**decimals1) / (reserve0 / 10**decimals0)
    else:
        return (reserve0 / 10**decimals0) / (reserve1 / 10**decimals1)

def simulate_order(price, buy=True):
    return price * (1 + SPREAD) if buy else price * (1 - SPREAD)

def calculate_profit(price_buy, price_sell):
    return (price_sell - price_buy) / price_buy * 100

# 🔹 Boucle principale paper trading
for iteration in range(5):
    price = get_price()
    buy_price = simulate_order(price, buy=True)
    sell_price = simulate_order(price, buy=False)
    profit = calculate_profit(buy_price, sell_price)

    print(f"\nIteration {iteration+1}")
    print(f"Prix spot simulé : {price:.2f} USDC/WETH")
    print(f"Ordre BUY simulé : {buy_price:.2f} USDC")
    print(f"Ordre SELL simulé : {sell_price:.2f} USDC")
    print(f"Profit simulé : {profit:.4f} %")
    time.sleep(5)
