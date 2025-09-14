from web3 import Web3
import json

# 🔹 RPC Sepolia
w3 = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"))
print("Connexion Sepolia :", w3.is_connected())

# 🔹 Adresses des tokens
token_in = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14"   # WETH 
token_out = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"  # USDC (Sepolia) 

# 🔹 Adresse du router Uniswap V2 (Sepolia)
router_address = "0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3" 

# 🔹 ABI minimale pour Router V2
router_abi = json.loads("""
[
  {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},
             {"internalType":"address[]","name":"path","type":"address[]"}],
   "name":"getAmountsOut",
   "outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"}],
   "stateMutability":"view",
   "type":"function"},
  {"inputs":[],"name":"factory",
   "outputs":[{"internalType":"address","name":"","type":"address"}],
   "stateMutability":"view",
   "type":"function"}
]
""")

# 🔹 ABI minimale pour Factory
factory_abi = json.loads("""
[
  {"inputs":[{"internalType":"address","name":"","type":"address"},
             {"internalType":"address","name":"","type":"address"}],
   "name":"getPair",
   "outputs":[{"internalType":"address","name":"","type":"address"}],
   "stateMutability":"view",
   "type":"function"}
]
""")

# 🔹 Contrats
router = w3.eth.contract(address=router_address, abi=router_abi)

def debug_pair(token_in, token_out):
    try:
        # Vérifie factory du router
        factory_address = router.functions.factory().call()
        print(f"Factory du router : {factory_address}")

        factory = w3.eth.contract(address=factory_address, abi=factory_abi)

        # Vérifie si un pool existe
        pair_address = factory.functions.getPair(token_in, token_out).call()
        if pair_address == "0x0000000000000000000000000000000000000000":
            print("⚠️ Aucun pool WETH/USDC trouvé sur ce router.")
            return

        print(f"Pool WETH/USDC trouvé : {pair_address}")

        # Tente de récupérer un prix
        amount_in = w3.to_wei(1, "ether")  # 1 WETH
        amounts = router.functions.getAmountsOut(amount_in, [token_in, token_out]).call()
        print(f"Prix obtenu : 1 WETH = {amounts[-1]} (USDC, 6 décimales)")
    except Exception as e:
        print(f"Erreur lors du debug : {e}")

# 🔹 Lancer debug
debug_pair(token_in, token_out)
