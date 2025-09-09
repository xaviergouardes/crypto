import asyncio
import websockets
import json
from binance.client import Client
import os
import math

# =========================
# CONFIG TESTNET
# =========================
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
client = Client(API_KEY, API_SECRET, testnet=True)

# Triplet d'arbitrage générique (ordre libre)
# PAIRS = ["BTCUSDT", "ETHBTC", "ETHUSDT"]
# PAIRS = ["BTCUSDC", "ACHBTC", "ACHUSDC"]
PAIRS = ["BTCUSDC", "SKLBTC", "SKLUSDC"]

KNOWN_QUOTES = ['USD', 'USDC', 'ACH', 'BTC', 'SKL'] 

FEE = 0.001       # 0.1% Binance
MIN_PROFIT = 0.007  # profit minimal 0.7%
BASE_AMOUNT = 1000   # montant initial (ex: USDT)

# =========================
# FONCTIONS UTILES
# =========================
async def get_order_book(pair):
    url = f"wss://stream.binance.com:9443/ws/{pair.lower()}@depth5@100ms"
    async with websockets.connect(url) as ws:
        msg = await ws.recv()
        data = json.loads(msg)
        bids = [(float(p[0]), float(p[1])) for p in data['bids']]
        asks = [(float(p[0]), float(p[1])) for p in data['asks']]
        print(f"Prix Brut : paire={pair} bids={bids[0][0]:.12f} asks={asks[0][0]:.12f}")
        return bids, asks

def get_assets_from_pairs(pairs):
    assets = set()
    for p in pairs:
        quote = None
        for q in KNOWN_QUOTES:
            if p.endswith(q):
                quote = q
                break
        if quote is None:
            raise ValueError(f"Impossible de détecter le quote pour {p}")
        base = p[:-len(quote)]
        assets.update([base, quote])
    return list(assets)

def get_balances(pairs):
    balances = client.get_account()['balances']
    result = {}
    assets = get_assets_from_pairs(pairs)
    for asset in assets:
        bal = next((float(b['free']) for b in balances if b['asset']==asset), 0)
        result[asset] = bal
    return result

def adjust_qty(symbol, qty):
    info = client.get_symbol_info(symbol)
    step_size = None
    min_qty = None
    for f in info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            step_size = float(f['stepSize'])
            min_qty = float(f['minQty'])
            break
    if step_size is None:
        return qty
    qty = math.floor(qty / step_size) * step_size
    decimals = int(round(-math.log10(step_size), 0))
    qty = round(qty, decimals)
    if qty < min_qty:
        qty = min_qty
    return qty

async def place_order(symbol, side, qty):
    try:
        return client.create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
    except Exception as e:
        print(f"Erreur sur {symbol}: {e}")
        return None

# =========================
# CALCUL DU PROFIT AUTOMATIQUE
# =========================
def calc_triangular_profit_auto(order_books, pairs, base_amount):
    """
    Teste les 2 directions possibles pour un triplet de paires
    et retourne la direction avec le profit maximal
    """
    def simulate_flow(order_books, flow):
        # flow = [(pair_index, 'BUY'/'SELL'), ...]
        amt = base_amount
        for idx, side in flow:
            bids, asks = order_books[idx]
            price = asks[0][0] if side=='BUY' else bids[0][0]
            amt = amt / price if side=='BUY' else amt * price
            amt *= (1 - FEE)
        return amt

    # Direction 1: pairs[0]->pairs[1]->pairs[2]
    flow1 = [(0,'BUY'), (1,'BUY'), (2,'SELL')]
    final1 = simulate_flow(order_books, flow1)
    profit1 = (final1 - base_amount)/base_amount

    # Direction 2: inverse flux (pairs[0]->pairs[1]->pairs[2] inversé)
    flow2 = [(0,'SELL'), (1,'SELL'), (2,'BUY')]
    final2 = simulate_flow(order_books, flow2)
    profit2 = (final2 - base_amount)/base_amount

    #print("Direction 1:", flow1, "Profit:", profit1*100, "%")
    #print("Direction 2:", flow2, "Profit:", profit2*100, "%")

    if profit1 > profit2:
        return profit1, final1, flow1
    else:
        return profit2, final2, flow2

# =========================
# EXECUTION DE L'ARBITRAGE
# =========================
async def execute_arbitrage():
    order_books = await asyncio.gather(*[get_order_book(p) for p in PAIRS])
    profit, final_amount, flow = calc_triangular_profit_auto(order_books, PAIRS, BASE_AMOUNT)
    print(f"Profit potentiel: {profit*100:.2f}% → {BASE_AMOUNT} → {final_amount:.4f}")

    if profit > MIN_PROFIT:
        print("💰 Opportunité détectée ! Envoi des ordres...")
        # Calcul des quantités ajustées pour chaque ordre
        qtys = []
        for idx, side in flow:
            bids, asks = order_books[idx]
            price = asks[0][0] if side=='BUY' else bids[0][0]
            amt = BASE_AMOUNT if idx==0 else qtys[-1]
            qty = amt / price if side=='BUY' else amt
            qty = adjust_qty(PAIRS[idx], qty)
            qtys.append(qty)
            print(f"{PAIRS[idx]} {side} qty={qty} price={price}")

        # Passer les ordres en parallèle
        await asyncio.gather(*[place_order(PAIRS[idx], side, qtys[i]) for i,(idx,side) in enumerate(flow)])

        balances_after = get_balances(PAIRS)
        print("💰 Soldes après arbitrage :", balances_after)
    else:
        print("Pas assez de profit, on attend...")

# =========================
# BOUCLE PRINCIPALE
# =========================
async def main_loop():
    balances_before = get_balances(PAIRS)
    print("💰 Soldes avant arbitrage :", balances_before)
    while True:
        await execute_arbitrage()
        await asyncio.sleep(0.5)

# =========================
# LANCEMENT
# =========================
if __name__ == "__main__":
    asyncio.run(main_loop())
