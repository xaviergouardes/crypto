import asyncio
import aiohttp
import time
import json
import os

# ================= CONFIG ===================
SYMBOL = "ethusdc"
REST_DEPTH = 150
WS_DEPTH = 10
PERSISTENCE_SECONDS = 10.0      # durée pour valider une zone
MIN_QTY = 0.05                  # quantité minimale pour considérer un niveau
ALERT_MULTIPLIER = 5.0           # seuil pour détecter un gros ordre
EMA_ALPHA = 0.1                  # lissage EMA
HEATMAP_LINES = 40               # nombre de lignes du heatmap

# ANSI colors
COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[31m"
COLOR_RESET = "\033[0m"

# ================ GLOBALS ==================
price_stats = {}        # dict: clé=side:price, valeur=détails du niveau
validated_zones = {}    # dict: clé=side:price, zones validées
last_update_id = None

# ================ UTIL =====================
def key_of(side: str, price: float) -> str:
    return f"{side}:{price:.8f}"

def now() -> float:
    return time.time()

def compute_score(qty, duration):
    return qty * duration

# ================ SNAPSHOT ==================
async def fetch_snapshot(session):
    url = f"https://api.binance.com/api/v3/depth?symbol={SYMBOL.upper()}&limit={REST_DEPTH}"
    async with session.get(url) as resp:
        data = await resp.json()
        return data

def process_snapshot_initial(snapshot):
    global last_update_id
    t = now()
    last_update_id = snapshot.get("lastUpdateId") or last_update_id
    bids = snapshot.get("bids") or []
    asks = snapshot.get("asks") or []
    for price_str, qty_str in bids:
        price = float(price_str)
        qty = float(qty_str)
        if qty < MIN_QTY:
            continue
        k = key_of("BID", price)
        price_stats[k] = {
            "side": "BID",
            "price": price,
            "ema_qty": qty,
            "first_seen": t,
            "last_seen": t,
            "qty": qty
        }
    for price_str, qty_str in asks:
        price = float(price_str)
        qty = float(qty_str)
        if qty < MIN_QTY:
            continue
        k = key_of("ASK", price)
        price_stats[k] = {
            "side": "ASK",
            "price": price,
            "ema_qty": qty,
            "first_seen": t,
            "last_seen": t,
            "qty": qty
        }
    print(f"[snapshot] loaded lastUpdateId={last_update_id}, bids={len(bids)}, asks={len(asks)}", flush=True)

# ================ WS UPDATE ==================
def process_ws_update_ws_snapshot(snapshot):
    global last_update_id
    t = now()
    last_update_id = snapshot.get("lastUpdateId", last_update_id)
    for side_key, side_name in [("bids", "BID"), ("asks", "ASK")]:
        for price_str, qty_str in snapshot.get(side_key, []):
            price = float(price_str)
            qty = float(qty_str)
            k = key_of(side_name, price)

            if qty < MIN_QTY:
                price_stats.pop(k, None)
                validated_zones.pop(k, None)
                continue

            rec = price_stats.get(k)
            if rec is None:
                # niveau jamais vu → on l'initialise
                price_stats[k] = {
                    "side": side_name,
                    "price": price,
                    "ema_qty": qty,
                    "first_seen": t,
                    "last_seen": t,
                    "qty": qty
                }
                rec = price_stats[k]

            # mise à jour de l'EMA et du temps
            rec["ema_qty"] = EMA_ALPHA * qty + (1 - EMA_ALPHA) * rec.get("ema_qty", qty)
            rec["last_seen"] = t
            rec["qty"] = qty

            # detection zone persistante
            ema = rec.get("ema_qty", 1e-9)
            if qty > ALERT_MULTIPLIER * ema:
                duration = t - rec["first_seen"]
                if duration >= PERSISTENCE_SECONDS:
                    score = compute_score(qty, duration)
                    if k not in validated_zones:
                        validated_zones[k] = {
                            "side": rec["side"],
                            "price": rec["price"],
                            "qty": rec["qty"],
                            "ema_qty": rec["ema_qty"],
                            "first_seen": rec["first_seen"],
                            "last_seen": rec["last_seen"],
                            "duration": duration,
                            "score": score
                        }
                        print(f"[zone detected] {validated_zones[k]}")
                    else:
                        vz = validated_zones[k]
                        vz.update({
                            "qty": rec["qty"],
                            "ema_qty": rec["ema_qty"],
                            "last_seen": rec["last_seen"],
                            "duration": t - rec["first_seen"],
                            "score": compute_score(rec["qty"], t - rec["first_seen"])
                        })
            else:
                if k in validated_zones:
                    del validated_zones[k]

# ================ MESSAGE HANDLER ==================
def handle_ws_message(data):
    if not isinstance(data, dict):
        return
    if "lastUpdateId" in data and ("bids" in data or "asks" in data):
        process_ws_update_ws_snapshot(data)

# ================ HEATMAP =====================
def print_heatmap():
    import os
    os.system("cls" if os.name == "nt" else "clear")
    
    all_prices = list(price_stats.values())
    if not all_prices:
        return
    
    min_price = min(p["price"] for p in all_prices)
    max_price = max(p["price"] for p in all_prices)
    step = (max_price - min_price) / HEATMAP_LINES if max_price != min_price else 1
    bins = [0] * HEATMAP_LINES
    symbols = [" "] * HEATMAP_LINES
    colors = [""] * HEATMAP_LINES

    # Calculer les bins
    for p in all_prices:
        idx = int((p["price"] - min_price) / step)
        if idx >= HEATMAP_LINES:
            idx = HEATMAP_LINES - 1
        bins[idx] += p["qty"]

    # Marquer les zones validées
    for vz in validated_zones.values():
        idx = int((vz["price"] - min_price) / step)
        if idx >= HEATMAP_LINES:
            idx = HEATMAP_LINES - 1
        if vz["side"] == "BID":
            symbols[idx] = "*"  # support
            colors[idx] = "\033[32m"  # vert
        else:
            symbols[idx] = "+"  # résistance
            colors[idx] = "\033[31m"  # rouge

    max_bin = max(bins) or 1

    print("====== HEATMAP ======")
    for i in reversed(range(HEATMAP_LINES)):
        bar_len = int((bins[i] / max_bin) * 50)
        if bar_len == 0:
            bar = ""
        else:
            color = colors[i]
            reset = "\033[0m"
            bar = "#" * (bar_len - 1) + (color + symbols[i] + reset)
        print(f"{min_price + i*step:8.4f} | {bar}")
    print("=====================")
    print(f"Validated zones: {len(validated_zones)}")



# ================ WS LOOP ==================
async def ws_loop():
    url = f"wss://stream.binance.com:9443/ws/{SYMBOL}@depth{WS_DEPTH}@100ms"
    async with aiohttp.ClientSession() as session:
        # fetch snapshot initial avant de lancer WS
        snapshot = await fetch_snapshot(session)
        process_snapshot_initial(snapshot)

        async with session.ws_connect(url) as ws:
            print("Connected to Binance WebSocket!", flush=True)
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    handle_ws_message(data)
                    print_heatmap()
                    await asyncio.sleep(0.1)  # pour voir le heatmap bouger
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    print(f"[ws_loop] WS closed/error: {msg.type}", flush=True)
                    break

# ================ MAIN ======================
if __name__ == "__main__":
    asyncio.run(ws_loop())
