import asyncio
import websockets
import json
from binance.client import Client
import os
import math
import json

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
client = Client(API_KEY, API_SECRET, testnet=True)

# PAIRS = ["ETHUSDC", "ETHBTC", "BTCUSDC"]
PAIRS = ["ACHUSDC", "ACHBTC", "BTCUSDC"]
#PAIRS = ["SKLUSDC", "SKLBTC", "BTCUSDC"]

FEE = 0.001
MIN_PROFIT = 0.007
BASE_AMOUNT = 100

KNOWN_QUOTES = ['USD', 'USDC', 'ACH', 'BTC', 'SKL', 'BNB', 'PLUME', 'AVAX'] 

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

async def place_order(symbol, side, qty):
    try:
        return client.create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
    except Exception as e:
        print(f"Erreur sur {symbol}: {e}")
        raise e

#def adjust_qty(symbol, qty):
#    print(f"symbol={symbol} qty={qty}")
#    info = client.get_symbol_info(symbol)
#    step_size = float([f['stepSize'] for f in info['filters'] if f['filterType']=='LOT_SIZE'][0])
#
#   qty = math.floor(qty / step_size) * step_size
#    print(f"step_size={step_size} / qty={qty}")
#    return qty

def adjust_qty(symbol, qty):
     print(f"symbol={symbol} qty={qty}")
 
     info = client.get_symbol_info(symbol)
     print(f"info={info}")
 
     step_size = None
     min_qty = None
     for f in info['filters']:
         if f['filterType'] == 'LOT_SIZE':
             step_size = float(f['stepSize'])
             min_qty = float(f['minQty'])
             break
     if step_size is None:
         return qty
 
     print(f"step_size={step_size}, min_qty={min_qty}")
 
     qty = math.floor(qty / step_size) * step_size
     decimals = int(round(-math.log10(step_size), 0))
     print(f"qty={qty} decimals={decimals}")
 
     qty = round(qty, decimals)
     if qty < min_qty:
        qty = min_qty

     print(f"qty={qty} decimals={decimals}")
     return qty

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

async def execute_arbitrage():
    # s'assurer que toutes les paires ont un prix
    if any(v is None for v in prices.values()):
        return

    bids1, asks1 = prices[PAIRS[0]]
    bids2, asks2 = prices[PAIRS[1]]
    bids3, asks3 = prices[PAIRS[2]]

    ask1 = asks1[0][0] # prix pour l'achat
    ask2 = asks2[0][0]
    bid2 = bids2[0][0] # prix pour la vente
    bid3 = bids3[0][0]

    eth_amount = (BASE_AMOUNT / ask1) * (1 - FEE)
    btc_amount = (eth_amount * ask2) * (1 - FEE)
    final_amount = btc_amount * bid3 * (1 - FEE)
    profit_pct = (final_amount - BASE_AMOUNT)/BASE_AMOUNT
    print(f"Quantité calculée : Achat ETH={eth_amount:.12f}, Vente BTC={eth_amount:.12f}, Vente ETH={btc_amount:.12f}")
    print(f"Profit potentiel : {profit_pct*100:.2f}% → final={final_amount:.4f} - prix {PAIRS[0]} ask1={ask1:.12f} - prix {PAIRS[1]} aks2={ask2:.12f} - prix {PAIRS[2]} bid3={bid3:.12f}")

    if profit_pct > MIN_PROFIT:
        try:
            eth_amount_buy = adjust_qty(PAIRS[0], BASE_AMOUNT / ask1)
            btc_amount_buy = adjust_qty(PAIRS[1], eth_amount * ask2 * (1 - FEE))
            btc_amount_sell = adjust_qty(PAIRS[2], (btc_amount_buy - btc_amount_buy * 0.021))
            final_amount_sell = btc_amount_sell * bid3

            print(f"Envoi des ordres: Achat de {eth_amount_buy:.12f} ACH avec 100 USDC, Vente de {eth_amount_buy:.12f} ACH récupération de {btc_amount_buy:.12f} BTC, Vente de {btc_amount_sell:.12f} BTC récupération de {final_amount_sell:.12f} USDC")
            orders = await asyncio.gather(
                place_order(PAIRS[0], 'BUY', eth_amount_buy),
                place_order(PAIRS[1], 'SELL', eth_amount_buy),
                place_order(PAIRS[2], 'SELL', btc_amount_sell)
            )
            result = {
                "order1:": orders[0],
                "order2:": orders[1],
                "order3:": orders[2]
            }
            #print(f"result : {json.dumps(result, ensure_ascii=False)}")
            print("💰 Soldes après arbitrage :", get_balances(PAIRS))
        except Exception as e:
            print(f"Erreur sur {symbol}: {e}")
            raise e

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
