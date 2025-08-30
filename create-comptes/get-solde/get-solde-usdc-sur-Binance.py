from web3 import Web3

# Endpoint RPC public BSC (tu peux aussi utiliser un provider comme Ankr, Quicknode, Blast, etc.)
BSC_RPC = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Vérification connexion
if not web3.is_connected():
    raise Exception("Connexion au réseau BSC échouée")

# Adresse à vérifier
address = web3.to_checksum_address("0xe42d1cb2B417D89f91FF7F23BC72cb3Fe12112bE")

# Contrat USDC BEP-20 (Binance-Peg USDC)
usdc_contract_address = web3.to_checksum_address("0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d")

# ABI minimale ERC-20
erc20_abi = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

# Contrat USDC
usdc_contract = web3.eth.contract(address=usdc_contract_address, abi=erc20_abi)

# Récupération du solde
balance = usdc_contract.functions.balanceOf(address).call()
decimals = usdc_contract.functions.decimals().call()
symbol = usdc_contract.functions.symbol().call()

# Conversion format humain
human_balance = balance / (10 ** decimals)

print(f"Solde {symbol} de {address} : {human_balance}")
