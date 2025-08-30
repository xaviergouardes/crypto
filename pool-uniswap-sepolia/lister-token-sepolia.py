from web3 import Web3

RPC_URL = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
]

token_address = "0x722b214d55deb458b7c86c4ac9426b4356314db3"  # exemple USDC Sepolia
token = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
print("Symbole:", token.functions.symbol().call())
print("Nom:", token.functions.name().call())
