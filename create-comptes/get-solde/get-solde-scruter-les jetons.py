from web3 import Web3

# Remplace par ton endpoint Sepolia (Infura, Alchemy ou autre)
INFURA_URL = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Transaction hash complet (mets bien le hash entier avec '0x...')
tx_hash = "0x6ac418cfec002eafa77260a4cdb1c4a248b2c736af9a417ccbdcb9af83de731e"

try:
    receipt = w3.eth.get_transaction_receipt(tx_hash)
except Exception as e:
    print("Erreur récupération receipt :", e)
    exit()

# Signature standard des transferts ERC20 : Transfer(address,address,uint256)
transfer_sig = w3.keccak(text="Transfer(address,address,uint256)").hex()

print(f"Analyse de la transaction {tx_hash}...\n")

for log in receipt["logs"]:
    if log["topics"][0].hex() == transfer_sig:
        contract_address = log["address"]

        # Essayer de lire le symbole du token
        try:
            token_contract = w3.eth.contract(address=contract_address, abi=[
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function",
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function",
                },
            ])
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
        except:
            symbol = "???"
            decimals = 18

        # Décoder la valeur transférée
        from_addr = "0x" + log["topics"][1].hex()[-40:]
        to_addr = "0x" + log["topics"][2].hex()[-40:]
        value = int(log["data"], 16) / (10 ** decimals)

        print(f"Token : {symbol} ({contract_address})")
        print(f"De : {from_addr}")
        print(f"À  : {to_addr}")
        print(f"Montant : {value}\n")
