from web3 import Web3
import json
import os

# --- Connexion à Sepolia ---
w3 = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"))
print("Connexion Sepolia :", w3.is_connected())

wallet_address = os.getenv("WALLET_ADDRESS")  
router_address = "0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3"  # adresse du router pour lequel tu veux vérifier l'allowance

# --- Contrat USDC Sepolia ---
token_address = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"

# ABI ERC-20 minimal pour allowance
erc20_abi = json.loads("""
[
  {
    "constant": true,
    "inputs": [
      {"name":"owner","type":"address"},
      {"name":"spender","type":"address"}
    ],
    "name":"allowance",
    "outputs":[{"name":"","type":"uint256"}],
    "payable":false,
    "stateMutability":"view",
    "type":"function"
  }
]
""")

token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)

# --- Lecture de l'allowance ---
try:
    allowance = token_contract.functions.allowance(wallet_address, router_address).call()
    print(f"Allowance actuelle pour le router : {allowance}")
except Exception as e:
    print("Erreur lors de la lecture de l'allowance :", e)
