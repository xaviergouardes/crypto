from web3 import Web3

# Même adresse pour les deux réseaux
address = "0x65390B0bb9420BD83b1325Bf05dF1b4A8b2938B4"

# --- Sepolia ---
sepolia_rpc = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"
w3_sepolia = Web3(Web3.HTTPProvider(sepolia_rpc))
balance_sepolia = w3_sepolia.eth.get_balance(address)
print(f"Solde Sepolia : {w3_sepolia.from_wei(balance_sepolia, 'ether')} ETH")

# --- BSC Testnet ---
bsc_rpc = "https://data-seed-prebsc-1-s1.binance.org:8545/"
w3_bsc = Web3(Web3.HTTPProvider(bsc_rpc))
balance_bsc = w3_bsc.eth.get_balance(address)
print(f"Solde BSC Testnet : {w3_bsc.from_wei(balance_bsc, 'ether')} BNB")