from web3 import Web3

RPC_URL = "https://rpc.hyperliquid-testnet.xyz/evm"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if w3.is_connected():
    print("✅ Connecté au testnet HyperEVM")
    print("Numéro du dernier bloc testnet :", w3.eth.block_number)
else:
    print("❌ Échec de connexion au testnet")