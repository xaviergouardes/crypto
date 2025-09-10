#!/usr/bin/env python3
"""
Bot simple d'exécution basé sur Order Imbalance (Testnet)
- WebSocket depth (depth5@100ms)
- Calcule imbalance = sum(bids_vol) / (sum(bids_vol) + sum(asks_vol))
- Si imbalance > BUY_THRESHOLD -> market BUY (consomme quote)
- Si imbalance < SELL_THRESHOLD -> market SELL (vend base)
- Respecte LOT_SIZE (stepSize, minQty)
- Affiche soldes avant/après
"""
import os
import asyncio
import websockets
import json
import math
import time
from binance.client import Client

# -------------------------
# CONFIG
# -------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    raise SystemExit("Set BINANCE_API_KEY and BINANCE_API_SECRET env variables")

# pair to trade (changeable)
#PAIR = os.getenv("PAIR", "BTCUSDT")    # exemple BTCUSDT
PAIR = os.getenv("PAIR", "BTCUSDT")    # exemple BTCUSDT

# Mode Testnet
client = Client(API_KEY, API_SECRET, testnet=True)

# Order imbalance parameters
DEPTH_LEVELS = 5                 # nombre de niveaux à sommer (depth5)
BUY_THRESHOLD = 0.65             # imbalance > -> buy
SELL_THRESHOLD = 0.35            # imbalance < -> sell
COOLDOWN_SECS = 3.0              # délai min entre ordres (pour éviter spam)

# Taille de l'ordre (en quote currency pour BUY, en base currency pour SELL)
QUOTE_ORDER_SIZE = 50.0          # ex: 50 USDT par ordre d'achat
MIN_PROFIT_MARGIN = 0.0          # non utilisé ici mais utile pour extensions

# -------------------------
# UTILITAIRES
# -------------------------
def get_balances_for_pair(pair):
    """Renvoie dict {asset: free_balance} pour la paire (base, quote)."""
    info = client.get_account()
    balances = {b['asset']: float(b['free']) for b in info['balances']}
    base, quote = split_pair(pair)
    return {base: balances.get(base, 0.0), quote: balances.get(quote, 0.0)}

def split_pair(pair):
    """
    Détecte automatiquement base/quote.
    Cherche parmi known quotes, sinon assume last 3 chars as quote.
    """
    KNOWN_QUOTES = ['USDT','USDC','BUSD','BTC','ETH','BNB']
    for q in KNOWN_QUOTES:
        if pair.endswith(q):
            base = pair[:-len(q)]
            return base, q
    # fallback
    return pair[:-3], pair[-3:]

def get_lot_filter(pair):
    info = client.get_symbol_info(pair)
    if not info:
        raise RuntimeError(f"No symbol info for {pair}")
    for f in info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            step = float(f['stepSize'])
            min_qty = float(f['minQty'])
            return step, min_qty
    return None, None

def adjust_qty_to_lot(pair, qty):
    """Arrondit qty à stepSize multiple et >= minQty."""
    step, min_qty = get_lot_filter(pair)
    if step is None:
        return qty
    # floor to step
    qty_adj = math.floor(qty / step) * step
    # round to decimals
    decimals = max(0, int(round(-math.log10(step))))
    qty_adj = round(qty_adj, decimals)
    if qty_adj < min_qty:
        # si inférieur au min_qty, renvoie 0 pour indiquer impossible
        return 0.0
    return qty_adj

async def place_market_buy(pair, quote_amount):
    """
    Place un market BUY sur pair en dépensant environ quote_amount (en quote currency).
    On calcule qty base = quote_amount / best_ask (approx).
    """
    # récuperer best ask via REST (rapide)
    ticker = client.get_order_book(symbol=pair, limit=5)
    best_ask = float(ticker['asks'][0][0])
    raw_qty = quote_amount / best_ask
    qty = adjust_qty_to_lot(pair, raw_qty)
    if qty <= 0:
        print("Quantité ajustée non valide (trop petite) pour BUY:", raw_qty)
        return None
    try:
        order = client.create_order(symbol=pair, side='BUY', type='MARKET', quantity=qty)
        return order
    except Exception as e:
        print("Erreur place_market_buy:", e)
        return None

async def place_market_sell(pair, base_qty):
    """Place un market SELL sur pair en vendant base_qty."""
    qty = adjust_qty_to_lot(pair, base_qty)
    if qty <= 0:
        print("Quantité ajustée non valide (trop petite) pour SELL:", base_qty)
        return None
    try:
        order = client.create_order(symbol=pair, side='SELL', type='MARKET', quantity=qty)
        return order
    except Exception as e:
        print("Erreur place_market_sell:", e)
        return None

def compute_order_imbalance(bids, asks, levels=DEPTH_LEVELS):
    """Calcule imbalance sur n niveaux: sum(bids_qty)/(sum(bids_qty)+sum(asks_qty))"""
    bids_vol = sum(q for _, q in bids[:levels])
    asks_vol = sum(q for _, q in asks[:levels])
    denom = bids_vol + asks_vol
    if denom == 0:
        return 0.5  # neutre si pas de volume
    return bids_vol / denom

# -------------------------
# BOT PRINCIPAL
# -------------------------
last_order_time = 0.0

async def ws_depth_listener(pair):
    """Écoute depth via websocket; génère signaux et passe ordres si conditions remplies."""
    global last_order_time
    url = f"wss://stream.binance.com:9443/ws/{pair.lower()}@depth5@100ms"
    print(f"Connecting to {url}")
    async with websockets.connect(url) as ws:
        async for msg in ws:
            try:
                data = json.loads(msg)
                bids = [(float(p[0]), float(p[1])) for p in data.get('bids', [])]
                asks = [(float(p[0]), float(p[1])) for p in data.get('asks', [])]
                if not bids or not asks:
                    continue
                imbalance = compute_order_imbalance(bids, asks)
                now = time.time()
                # affichage synthétique
                best_bid = bids[0][0]
                best_ask = asks[0][0]
                #print(f"[{pair}] ask={best_ask:.8f} bid={best_bid:.8f} imbalance={imbalance:.3f}")

                # cooldown
                if now - last_order_time < COOLDOWN_SECS:
                    continue

                # read balances before decision (for info)
                balances_before = get_balances_for_pair(pair)
                # Decision buy
                if imbalance > BUY_THRESHOLD:
                    print("Signal BUY (imbalance >", BUY_THRESHOLD, ")")
                    order = await place_market_buy(pair, QUOTE_ORDER_SIZE)
                    if order:
                        last_order_time = time.time()
                        print("Order BUY result:", {"status": order.get('status'), "fills": order.get('fills')})
                        balances_after = get_balances_for_pair(pair)
                        print("Balances before:", balances_before, "after:", balances_after)
                # Decision sell: only if we have base asset
                elif imbalance < SELL_THRESHOLD:
                    base, quote = split_pair(pair)
                    balances_before = get_balances_for_pair(pair)
                    base_bal = balances_before.get(base, 0.0)
                    # decide sell quantity: try to sell a fraction (ex: min(base_bal, qty_from_quote))
                    if base_bal <= 0:
                        # nothing to sell
                        continue
                    sell_qty = adjust_qty_to_lot(pair, base_bal * 0.5)  # vend 50% du base disponible
                    if sell_qty <= 0:
                        continue
                    print("Signal SELL (imbalance <", SELL_THRESHOLD, ")")
                    order = await place_market_sell(pair, sell_qty)
                    if order:
                        last_order_time = time.time()
                        print("Order SELL result:", {"status": order.get('status'), "fills": order.get('fills')})
                        balances_after = get_balances_for_pair(pair)
                        print("Balances before:", balances_before, "after:", balances_after)
                # else: no signal
            except Exception as e:
                print("Erreur message WS:", e)
                # on attend un peu avant de reconnecter si erreur persistante
                await asyncio.sleep(0.1)

# -------------------------
# LANCEMENT
# -------------------------
async def main():
    print("Starting OrderImbalance bot on", PAIR)
    # show initial balances
    print("Initial balances:", get_balances_for_pair(PAIR))
    await ws_depth_listener(PAIR)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
