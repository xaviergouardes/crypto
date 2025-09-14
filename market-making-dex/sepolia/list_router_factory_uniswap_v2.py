from web3 import Web3
import json

# 🔹 Connexion RPC Sepolia
sepolia_rpc = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"
w3 = Web3(Web3.HTTPProvider(sepolia_rpc))
if not w3.is_connected():
    raise Exception("❌ Connexion échouée")
print("✅ Connexion Sepolia :", w3.is_connected())

# 🔹 Liste de routers à tester
routers = [
    {"name": "Uniswap V2 Sepolia", "address": "0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3"},
    # ajouter d'autres routers connus ici
]

# 🔹 ABI minimale du router pour récupérer la factory
router_abi = json.loads("""
[{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],
  "stateMutability":"view","type":"function"}]
""")

# 🔹 Lister routers et factories
for r in routers:
    router = w3.eth.contract(address=r["address"], abi=router_abi)
    try:
        factory_address = router.functions.factory().call()
        print(f"Router: {r['name']} ({r['address']}) -> Factory: {factory_address}")
    except Exception as e:
        print(f"⚠️ Erreur pour router {r['name']} ({r['address']}): {e}")
