from web3 import Web3
from web3.exceptions import ContractLogicError

# --- Connexion RPC Sepolia ---
RPC_URL = "https://sepolia.infura.io/v3/f76b0853152040bdae32cd27f82a2d8a"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    print("❌ Échec de connexion au RPC Sepolia")
    exit()
print("✅ Connecté à Sepolia via Infura")

# --- Factory Uniswap V3 Sepolia ---
FACTORY_ADDRESS = "0x0227628f3F023bb0B980b67D528571c95c6DaC1c"
FACTORY_ABI = [
    {
        "inputs":[
            {"internalType":"address","name":"tokenA","type":"address"},
            {"internalType":"address","name":"tokenB","type":"address"},
            {"internalType":"uint24","name":"fee","type":"uint24"}
        ],
        "name":"getPool",
        "outputs":[{"internalType":"address","name":"pool","type":"address"}],
        "stateMutability":"view",
        "type":"function"
    }
]

factory = w3.eth.contract(address=w3.to_checksum_address(FACTORY_ADDRESS), abi=FACTORY_ABI)

# --- Fonction pour récupérer le symbole d'un token ---
ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"}
]

def get_symbol(token_address):
    try:
        token = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        return token.functions.symbol().call()
    except:
        return token_address[:6] + "..."  # fallback à l'adresse tronquée

# --- Liste des tokens connus sur Sepolia ---
TOKENS = [
    "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",  # WETH Sepolia 
    "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",  # USDC Sepolia (nouvelle version)
    "0x961751C387cA48617CcC527d11b0ECBb1952838F",  # Symbole: UNI-V2 , Nom: Uniswap V2
    "0x3f063c248f13ea4a6b2ca39084b3cbee23c2d9fa",  # Symbole: FYRE , Nom: FYRECOIN 
    "0x9cc6d3f7ee2dac12425ce6ced7a94b1376ca9ee1",  # Symbole: SEE , Nom: See
    "0x722b214d55deb458b7c86c4ac9426b4356314db3",  # Symbole: ARMT4 , Nom: ArmenianToken4
]

FEE_TIERS = [500, 3000, 10000]  # 0.05%, 0.3%, 1%

# --- Scan de tous les pools possibles ---
for i in range(len(TOKENS)):
    for j in range(i+1, len(TOKENS)):
        tokenA_addr = w3.to_checksum_address(TOKENS[i])
        tokenB_addr = w3.to_checksum_address(TOKENS[j])
        tokenA_symbol = get_symbol(tokenA_addr)
        tokenB_symbol = get_symbol(tokenB_addr)
        for fee in FEE_TIERS:
            try:
                pool = factory.functions.getPool(tokenA_addr, tokenB_addr, fee).call()
                if int(pool, 16) != 0:
                    print(f"✅ Pool trouvé : {pool} pour {tokenA_symbol} / {tokenB_symbol} avec fee {fee}")
            except ContractLogicError:
                pass  # ne rien afficher si erreur
