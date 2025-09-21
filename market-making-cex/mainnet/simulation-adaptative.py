import asyncio
import pandas as pd
import numpy as np
from binance import AsyncClient, BinanceSocketManager

API_KEY = ""
API_SECRET = ""

# Paramètres de base
# SYMBOL = "BTCUSDC"
# BASE_SPREAD = 0.00005    # spread minimal
MAX_SPREAD = 0.001       # spread maximal
# BASE_CYCLE = 10          # secondes
MIN_CYCLE = 9
MAX_CYCLE = 60
# CAPITAL = 1000           # USDT par trade

SYMBOL = "ETHBTC"
BASE_SPREAD = 0.00005
BASE_CYCLE = 50
CAPITAL = 1000

# Variables globales
prices = []          # stockage des ticks du cycle
trades = []          # historique des trades
open_buy = None
open_sell = None

# Calcul volatilité relative
def calculate_volatility(prices):
    if len(prices) < 2:
        return 0
    return np.std(prices) / np.mean(prices)


async def handle_trades(bsm):
    global prices
    ts = bsm.trade_socket(SYMBOL.lower())
    await ts.__aenter__()
    try:
        while True:
            msg = await ts.recv()
            try:
                price = float(msg['p'])
                prices.append(price)
            except Exception:
                continue
    finally:
        await ts.__aexit__(None, None, None)


async def strategy_loop():
    global prices, open_buy, open_sell, trades
    while True:
        if not prices:
            await asyncio.sleep(BASE_CYCLE)
            print(f"⚠️ Cycle vide | ticks=0")
            continue

        price_start = prices[0]
        price_end = prices[-1]
        min_price = min(prices)
        max_price = max(prices)
        ticks_count = len(prices)

        # Calcul volatilité et spread dynamique
        vol = calculate_volatility(prices)
        spread_value = min(BASE_SPREAD + vol, MAX_SPREAD)
        spread_pct = spread_value * 2 * 100

        # Cycle dynamique pour next iteration
        next_cycle = int(np.clip(BASE_CYCLE / (1 + vol*10), MIN_CYCLE, MAX_CYCLE))

        # Niveaux ordres
        buy_price = price_start * (1 - spread_value)
        sell_price = price_start * (1 + spread_value)

        # Placer les ordres si non existants
        open_buy = {"level": buy_price, "executed": False} if open_buy is None else open_buy
        open_sell = {"level": sell_price, "executed": False} if open_sell is None else open_sell

        # Ligne 1 : ordre positionné avec spread et cycle dynamique
        print(
            f"📝 Ordres positionnés price={price_start:.2f} | "
            f"BUY={open_buy['level']:.2f} SELL={open_sell['level']:.2f} "
            f"(spread={spread_value:.6f}, {spread_pct:.4f}%, cycle={next_cycle}s, "
            f"ticks={ticks_count}, min={min_price:.2f}, max={max_price:.2f})"
        )

        # Vérifier exécution des ordres
        executed_orders = []

        if not open_buy["executed"] and min_price <= open_buy["level"]:
            open_buy["executed"] = True
            executed_orders.append(("BUY", open_buy["level"]))

        if not open_sell["executed"] and max_price >= open_sell["level"]:
            open_sell["executed"] = True
            executed_orders.append(("SELL", open_sell["level"]))

        # Trade exécuté si les deux ordres touchés
        if open_buy["executed"] and open_sell["executed"]:
            pnl_buy = CAPITAL * (open_sell["level"] - open_buy["level"]) / open_buy["level"]
            print(
                f"✅ Trade exécuté BUY & SELL | BUY={open_buy['level']:.2f} SELL={open_sell['level']:.2f} "
                f"(PnL={pnl_buy:.2f} USDT, ticks={ticks_count}, min={min_price:.2f}, max={max_price:.2f})"
            )
            trades.append({
                "side": "BUY_SELL",
                "buy_entry": open_buy["level"],
                "sell_entry": open_sell["level"],
                "exit_market": price_end,
                "min_price": min_price,
                "max_price": max_price,
                "pnl": pnl_buy
            })
            open_buy = None
            open_sell = None

        # Fermeture marché si un seul ordre exécuté
        else:
            # BUY seul
            if open_buy["executed"] and (open_sell is None or not open_sell["executed"]):
                pnl_fermeture = CAPITAL * (price_end - open_buy["level"]) / open_buy["level"]
                print(f"🔒 Fermeture de l'ordre BUY au marché {price_end:.2f} (PnL fermeture={pnl_fermeture:.2f} USDT)")
                trades.append({
                    "side": "BUY",
                    "entry": open_buy["level"],
                    "exit_market": price_end,
                    "min_price": min_price,
                    "max_price": max_price,
                    "pnl_fermeture": pnl_fermeture
                })
                open_buy = None

            # SELL seul
            elif open_sell["executed"] and (open_buy is None or not open_buy["executed"]):
                pnl_fermeture = CAPITAL * (open_sell["level"] - price_end) / open_sell["level"]
                print(f"🔒 Fermeture de l'ordre SELL au marché {price_end:.2f} (PnL fermeture={pnl_fermeture:.2f} USDT)")
                trades.append({
                    "side": "SELL",
                    "entry": open_sell["level"],
                    "exit_market": price_end,
                    "min_price": min_price,
                    "max_price": max_price,
                    "pnl_fermeture": pnl_fermeture
                })
                open_sell = None

            if not executed_orders:
                print(f"❌ Aucun trade déclenché ce cycle")

        # Sauvegarde CSV toutes les 50 trades
        if len(trades) > 0 and len(trades) % 50 == 0:
            pd.DataFrame(trades).to_csv("trades.csv", index=False)
            print("💾 Sauvegarde des résultats dans trades.csv")

        # Reset ticks pour le prochain cycle
        prices = []

        # Attendre le cycle dynamique
        await asyncio.sleep(next_cycle)


async def main():
    client = await AsyncClient.create(API_KEY, API_SECRET)
    bsm = BinanceSocketManager(client)
    await asyncio.gather(handle_trades(bsm), strategy_loop())
    await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
