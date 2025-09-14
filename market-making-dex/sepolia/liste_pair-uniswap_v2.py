import json
from web3 import Web3

# 🔹 Connexion RPC Sepolia
sepolia_rpc = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"
w3 = Web3(Web3.HTTPProvider(sepolia_rpc))

if not w3.is_connected():
    raise Exception("❌ Connexion au réseau Sepolia échouée")
print("✅ Connexion Sepolia :", w3.is_connected())

# 🔹 Router Uniswap V2 (Sepolia)
router_address = Web3.to_checksum_address("0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3")

# ABI minimale du router
router_abi = json.loads("""
[{"inputs": [], "name": "factory", "outputs": [{"internalType": "address","name": "","type": "address"}],
  "stateMutability": "view","type": "function"}]
""")
router = w3.eth.contract(address=router_address, abi=router_abi)

# 🔹 Factory du router
factory_address = router.functions.factory().call()
print("🏭 Factory du router :", factory_address)

# 🔹 ABI factory
factory_abi = json.loads("""
[
  {"constant": true,"inputs": [],"name": "allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
   "stateMutability": "view","type": "function"},
  {"constant": true,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],
   "name": "allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],
   "stateMutability": "view","type": "function"}
]
""")
factory = w3.eth.contract(address=factory_address, abi=factory_abi)

# 🔹 ABI paire
pair_abi = json.loads("""
[
  {"constant": true,"inputs": [],"name": "token0","outputs":[{"internalType":"address","name":"","type":"address"}],
   "stateMutability": "view","type": "function"},
  {"constant": true,"inputs": [],"name": "token1","outputs":[{"internalType":"address","name":"","type":"address"}],
   "stateMutability": "view","type": "function"},
  {"constant": true,"inputs": [],"name": "getReserves",
   "outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},
              {"internalType":"uint112","name":"_reserve1","type":"uint112"},
              {"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],
   "stateMutability": "view","type": "function"}
]
""")

# 🔹 ABI minimal ERC20
erc20_abi = json.loads("""
[
  {"constant": true,"inputs": [],"name": "symbol","outputs":[{"name":"","type":"string"}],
   "stateMutability": "view","type": "function"},
  {"constant": true,"inputs": [],"name": "decimals","outputs":[{"name":"","type":"uint8"}],
   "stateMutability": "view","type": "function"}
]
""")

# 🔹 Récupération de toutes les paires
total_pairs = factory.functions.allPairsLength().call()
print(f"🔎 Nombre total de paires : {total_pairs}\n")

for i in range(total_pairs):
    pair_address = factory.functions.allPairs(i).call()
    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)

    try:
        token0_addr = pair_contract.functions.token0().call()
        token1_addr = pair_contract.functions.token1().call()

        # Vérifie la liquidité
        reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
        if reserve0 == 0 or reserve1 == 0:
            continue  # ignore les paires sans liquidité

        # Crée contrats ERC20 pour token0 & token1
        token0 = w3.eth.contract(address=token0_addr, abi=erc20_abi)
        token1 = w3.eth.contract(address=token1_addr, abi=erc20_abi)

        # Récupère symbol et décimales
        try:
            symbol0 = token0.functions.symbol().call()
            decimals0 = token0.functions.decimals().call()
        except:
            symbol0, decimals0 = "???", "?"

        try:
            symbol1 = token1.functions.symbol().call()
            decimals1 = token1.functions.decimals().call()
        except:
            symbol1, decimals1 = "???", "?"

        print(f"#{i}  Pair: {pair_address}")
        print(f"   token0: {token0_addr} ({symbol0}, decimals={decimals0}, reserve={reserve0})")
        print(f"   token1: {token1_addr} ({symbol1}, decimals={decimals1}, reserve={reserve1})\n")

    except Exception as e:
        print(f"⚠️ Erreur lecture paire {i} : {e}")
