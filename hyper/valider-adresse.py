from web3 import Web3

w3 = Web3()

# Adresse à tester
address = "0xb9f2e2b5af029e9ad090269dad41c4df"

# Vérification du format
if w3.is_checksum_address(address):
    print("✅ Adresse valide")
else:
    print("❌ Adresse invalide")