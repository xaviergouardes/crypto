import asyncio
import websockets
import json
from binance.client import Client
import os
import math

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
client = Client(API_KEY, API_SECRET, testnet=True)

PAIRS = ["SKLBTC", "ETHSKL", "ETHBTC"]
FEE = 0.001
MIN_PROFIT = 0.007
BASE_AMOUNT = 100

# dictionnaire global pour stocker les prix
prices = {pair: None for pair in PAIRS}

async def ws_order_book(pair):
    url = f"wss://stream.binance.com:9443/ws/{pair.lower()}@depth5@100ms"
    async with websockets.connect(url) as ws:
        async for msg in ws:
            data = json.loads(msg)
            bids = [(float(p[0]), float(p[1])) for p in data['bids']]
            asks = [(float(p[0]), float(p[1])) for p in data['asks']]
            prices[pair] = (bids, asks)

async def execute_arbitrage():
    # s'assurer que toutes les paires ont un prix
    if any(v is None for v in prices.values()):
        return
    bids1, asks1 = prices[PAIRS[0]]
    bids2, asks2 = prices[PAIRS[1]]
    bids3, asks3 = prices[PAIRS[2]]

    ask1 = asks1[0][0]
    bid2 = bids2[0][0]
    bid3 = bids3[0][0]

    btc_amount = (BASE_AMOUNT / ask1) * (1 - FEE)
    eth_amount = (btc_amount / bid2) * (1 - FEE)
    final_amount = eth_amount * bid3 * (1 - FEE)
    profit_pct = (final_amount - BASE_AMOUNT)/BASE_AMOUNT
    print(f"Profit potentiel: {profit_pct*100:.2f}% → final={final_amount:.4f}")

    if profit_pct > MIN_PROFIT:
        qty1 = adjust_qty(PAIRS[0], BASE_AMOUNT / ask1)
        qty2 = adjust_qty(PAIRS[1], qty1 / bid2)
        print(f"Envoi des ordres: {PAIRS[0]}={qty1}, {PAIRS[1]}={qty2}")
        await asyncio.gather(
            place_order(PAIRS[0], 'BUY', qty1),
            place_order(PAIRS[1], 'BUY', qty2),
            place_order(PAIRS[2], 'SELL', qty2)
        )

def adjust_qty(symbol, qty):
    info = client.get_symbol_info(symbol)
    step_size = float([f['stepSize'] for f in info['filters'] if f['filterType']=='LOT_SIZE'][0])
    qty = math.floor(qty / step_size) * step_size
    return qty

async def arbitrage_loop():
    while True:
        await execute_arbitrage()
        await asyncio.sleep(0.05)  # petite pause pour limiter la charge CPU

async def main():
    # lancer un WebSocket par paire + boucle arbitrage
    tasks = [ws_order_book(pair) for pair in PAIRS]
    tasks.append(arbitrage_loop())
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
