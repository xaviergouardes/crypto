from web3 import Web3
from eth_account import Account
import secrets

# Générer une clé privée aléatoire
private_key = "0x" + secrets.token_hex(32)

# Créer un compte à partir de la clé privée
account = Account.from_key(private_key)

print("Adresse Polygon :", account.address)
print("Clé privée :", account.key.hex())