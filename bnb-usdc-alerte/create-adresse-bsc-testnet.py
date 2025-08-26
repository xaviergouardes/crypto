from web3 import Web3

# Créer un compte Ethereum compatible BSC
account = Web3().eth.account.create()
print("Adresse :", account.address)
print("Clé privée :", account.key.hex())

#Adresse : 0x9e428f4042Be817983C2a810eDeA37CBa6aB940E
#Clé privée : 72475f76b8527af9410651a1fc935745db94156b98f4c6bb2276b6a3a0937c0d