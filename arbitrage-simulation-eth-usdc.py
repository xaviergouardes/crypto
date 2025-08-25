import asyncio
from decimal import Decimal
from web3 import Web3
import ccxt.async_support as ccxt
from datetime import datetime

# =========================
# CONSTANTES
# =========================
ETH_RPC_URL = "https://mainnet.infura.io/v3/3bdc55739dab4115ad4b202733a69938"
BINANCE_TAKER_FEE_BPS = Decimal("10")   # 0.10 %
UNISWAP_FEE_BPS = Decimal("5")          # 0.05 %
THRESHOLD_BPS = Decimal("15")           # 0.20 % minimum pour signal
BINANCE_MARKET = "ETH/USDC"

# =========================
# Solde initial USDC
# =========================
balance_usdc = Decimal("10000")

# =========================
# Connexion Web3
# =========================
w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))

# =========================
# Uniswap V3 Pool ETH/USDC 0.05%
# =========================
POOL_ADDRESS = Web3.to_checksum_address("0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8")
POOL_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
pool_contract = w3.eth.contract(address=POOL_ADDRESS, abi=POOL_ABI)

# =========================
# Fonctions pour récupérer prix
# =========================
async def fetch_binance_price(binance):
    ticker = await binance.fetch_ticker(BINANCE_MARKET)
    return Decimal(str(ticker['last']))

def fetch_uniswap_price_sync():
    slot0 = pool_contract.functions.slot0().call()
    sqrtPriceX96 = slot0[0]
    price = (Decimal(2**192) / Decimal(sqrtPriceX96)**2) * Decimal(10**12)
    return price.quantize(Decimal("0.01"))

async def fetch_uniswap_price():
    return await asyncio.to_thread(fetch_uniswap_price_sync)

# =========================
# Génération et simulation du signal
# =========================
def generate_signal(price_binance, price_dex):
    global balance_usdc
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fee_binance = BINANCE_TAKER_FEE_BPS / Decimal("10000")
    fee_uniswap = UNISWAP_FEE_BPS / Decimal("10000")

    # Déterminer BUY/SELL
    if price_binance > price_dex:
        buy_price, sell_price = price_dex, price_binance
        buy_venue, sell_venue = "DEX", "Binance"
    else:
        buy_price, sell_price = price_binance, price_dex
        buy_venue, sell_venue = "Binance", "DEX"

    # Calcul quantité ETH achetable avec tout le solde USDC
    if buy_venue == "DEX":
        trade_eth = balance_usdc / (buy_price * (Decimal("1") + fee_uniswap))
    else:
        trade_eth = balance_usdc / (buy_price * (Decimal("1") + fee_binance))

    gain_brut = (sell_price - buy_price) * trade_eth
    total_fees = trade_eth * ((price_binance * fee_binance) + (price_dex * fee_uniswap))
    pnl_net = gain_brut - total_fees
    diff_bps = ((sell_price - buy_price) / buy_price) * Decimal("10000")
    edge_after_fees_bps = diff_bps - (BINANCE_TAKER_FEE_BPS + UNISWAP_FEE_BPS)

    signal = f"[{timestamp}] NO TRADE — PnL net négatif ou inférieur au seuil"

    if pnl_net > 0 and edge_after_fees_bps >= THRESHOLD_BPS and trade_eth > 0:
        # Mise à jour du solde USDC
        if buy_venue == "DEX":
            usdc_spent = trade_eth * buy_price * (Decimal("1") + fee_uniswap)
            usdc_received = trade_eth * sell_price * (Decimal("1") - fee_binance)
        else:
            usdc_spent = trade_eth * buy_price * (Decimal("1") + fee_binance)
            usdc_received = trade_eth * sell_price * (Decimal("1") - fee_uniswap)

        balance_usdc = balance_usdc - usdc_spent + usdc_received

        signal = f"""[{timestamp}] SIGNAL ARB — BUY sur {buy_venue}, SELL sur {sell_venue}
Prix Binance: {price_binance:.2f} USDC/ETH
Prix DEX: {price_dex:.2f} USDC/ETH
Gain brut: {gain_brut:.2f} USDC
PnL net après frais: {pnl_net:.2f} USDC
Écart net après frais: {edge_after_fees_bps:.2f} bps
Quantité ETH tradée: {trade_eth:.4f} ETH
Solde USDC: {balance_usdc:.2f}"""

    return signal

# =========================
# Boucle principale
# =========================
async def main_loop():
    global balance_usdc
    print(f"Solde initial USDC: {balance_usdc:.2f}\n")
    binance = ccxt.binance()
    try:
        while True:
            price_binance, price_dex = await asyncio.gather(
                fetch_binance_price(binance),
                fetch_uniswap_price()
            )

            print("=== PRIX ===")
            print(f"Binance: {price_binance:.2f} USDC/ETH")
            print(f"DEX    : {price_dex:.2f} USDC/ETH")
            print("=== SIGNAL ===")
            print(generate_signal(price_binance, price_dex))
            print("\n---\n")

            await asyncio.sleep(2)
    finally:
        await binance.close()

if __name__ == "__main__":
    asyncio.run(main_loop())
