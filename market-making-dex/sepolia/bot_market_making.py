import os
from web3 import Web3
import time
import json

# 🔹 Récupération des variables d'environnement
private_key = os.getenv("PRIVATE_KEY")
wallet_address = os.getenv("WALLET_ADDRESS")  

if not private_key or not wallet_address:
    raise ValueError("Variables d'environnement PRIVATE_KEY et WALLET_ADDRESS doivent être définies !")

# 🔹 Connexion Sepolia via Infura
sepolia_rpc = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"
w3 = Web3(Web3.HTTPProvider(sepolia_rpc))
if not w3.is_connected():
    raise ConnectionError("Connexion au réseau Sepolia échouée !")
print("Connexion Sepolia :", w3.is_connected())
print("Bloc actuel :", w3.eth.block_number)

# 🔹 Router Uniswap V2 Sepolia
router_address = Web3.to_checksum_address("0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3") 
router_abi = [
    # getAmountsOut
    {
        "inputs":[
            {"internalType":"uint256","name":"amountIn","type":"uint256"},
            {"internalType":"address[]","name":"path","type":"address[]"}
        ],
        "name":"getAmountsOut",
        "outputs":[
            {"internalType":"uint256[]","name":"","type":"uint256[]"}
        ],
        "stateMutability":"view",
        "type":"function"
    },
    # swapExactTokensForTokens
    {
        "inputs":[
            {"internalType":"uint256","name":"amountIn","type":"uint256"},
            {"internalType":"uint256","name":"amountOutMin","type":"uint256"},
            {"internalType":"address[]","name":"path","type":"address[]"},
            {"internalType":"address","name":"to","type":"address"},
            {"internalType":"uint256","name":"deadline","type":"uint256"}
        ],
        "name":"swapExactTokensForTokens",
        "outputs":[
            {"internalType":"uint256[]","name":"","type":"uint256[]"}
        ],
        "stateMutability":"nonpayable",
        "type":"function"
    },
    # swapExactETHForTokens
    {
        "inputs":[
            {"internalType":"uint256","name":"amountOutMin","type":"uint256"},
            {"internalType":"address[]","name":"path","type":"address[]"},
            {"internalType":"address","name":"to","type":"address"},
            {"internalType":"uint256","name":"deadline","type":"uint256"}
        ],
        "name":"swapExactETHForTokens",
        "outputs":[
            {"internalType":"uint256[]","name":"","type":"uint256[]"}
        ],
        "stateMutability":"payable",
        "type":"function"
    },
    # swapExactTokensForETH
    {
        "inputs":[
            {"internalType":"uint256","name":"amountIn","type":"uint256"},
            {"internalType":"uint256","name":"amountOutMin","type":"uint256"},
            {"internalType":"address[]","name":"path","type":"address[]"},
            {"internalType":"address","name":"to","type":"address"},
            {"internalType":"uint256","name":"deadline","type":"uint256"}
        ],
        "name":"swapExactTokensForETH",
        "outputs":[
            {"internalType":"uint256[]","name":"","type":"uint256[]"}
        ],
        "stateMutability":"nonpayable",
        "type":"function"
    }
]
router = w3.eth.contract(address=router_address, abi=router_abi)

# 🔹 Tokens Sepolia
token_in = Web3.to_checksum_address("0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238")  # USDC Sepolia
decimals_in = 6
token_out = Web3.to_checksum_address("0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6")  # WETH Sepolia
decimals_out = 18
base_amount = 50 * 10**decimals_in  # 50 USDC

# 🔹 ERC20 minimal ABI pour approve et balanceOf
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
  },
  {
    "constant": false,
    "inputs": [
      {"name":"spender","type":"address"},
      {"name":"amount","type":"uint256"}
    ],
    "name":"approve",
    "outputs":[{"name":"","type":"bool"}],
    "payable":false,
    "stateMutability":"nonpayable",
    "type":"function"
  }
]
""")
token_in_contract = w3.eth.contract(address=token_in, abi=erc20_abi)

# 🔹 Approve automatique USDC
def approve_token(amount):
    print("approve_token ...")

    # Vérifie combien le router est autorisé à dépenser
    allowance = token_in_contract.functions.allowance(wallet_address, router_address).call()
    print(f"Allowance actuelle : {allowance}")

    if allowance < amount:
        nonce = w3.eth.get_transaction_count(wallet_address)
        tx = token_in_contract.functions.approve(router_address, amount).build_transaction({
            'from': wallet_address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Approval envoyé, tx hash: {tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Approval confirmé !")
        # tx ad98e3d917cbbef2a6aa884f200336900297eb9b7383e4d5266486965257e79f
    else:
        print("Allowance suffisante, pas besoin d'approuver.")


# 🔹 Obtenir prix WETH/USDC
def get_price(router, amount):
    print("get_price ...")
    amounts = router.functions.getAmountsOut(amount, [token_in, token_out]).call()
    print(f"price={amounts}")
    return amounts[-1]

# 🔹 Placer ordre BUY ou SELL
def place_order(router, amount_in, buy=True, spread=0.005):
    price = get_price(router, amount_in)
    min_out = int(price * (1 - spread)) if buy else int(price * (1 + spread))

    nonce = w3.eth.get_transaction_count(wallet_address)
    tx = router.functions.swapExactTokensForTokens(
        amount_in,
        min_out,
        [token_in, token_out] if buy else [token_out, token_in],
        wallet_address,
        w3.eth.getBlock('latest')['timestamp'] + 60*10
    ).build_transaction({
        'from': wallet_address,
        'gas': 200000,
        'gasPrice': w3.toWei('10', 'gwei'),
        'nonce': nonce
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Ordre {'BUY' if buy else 'SELL'} envoyé, tx hash: {tx_hash.hex()}")
    return price

# 🔹 Calcul profit simulé
def calculate_profit(price_buy, price_sell):
    return (price_sell - price_buy) / price_buy * 100

# 🔹 Paramètre : nombre d'itérations (None pour infini)
max_iterations = 1  # ou mettre un nombre, ex: 10

iteration = 0
while True:
    try:
        if max_iterations is not None and iteration >= max_iterations:
            print("Nombre maximum d'itérations atteint. Fin du bot.")
            break

        approve_token(base_amount)
        print(f"approve_token")

        current_price = get_price(router, base_amount)
        print(f"get_price")

        adjusted_spread = 0.005 + (current_price / 1000)

        print(f"Iteration {iteration+1}, Prix actuel WETH/USDC : {current_price}, Spread : {adjusted_spread:.4f}")

        price_buy = place_order(router, base_amount, buy=True, spread=adjusted_spread)
        print(f"price_buy")
        price_sell = place_order(router, base_amount, buy=False, spread=adjusted_spread)
        print(f"price_buy")

        profit_simule = calculate_profit(price_buy, price_sell)
        print(f"Profit simulé : {profit_simule:.4f} %\n")

        iteration += 1
        time.sleep(30)
    except Exception as e:
        print("Erreur :", e)
        time.sleep(10)
