import asyncio
import pandas as pd
from binance import AsyncClient, BinanceSocketManager

API_KEY = ""
API_SECRET = ""

# Paramètres stratégie
SYMBOL = "BTCUSDC"
CYCLE = 50          # secondes
SPREAD = 0.00005    # +/- 0.005%
CAPITAL = 1000      # USDT par trade

# Variables globales
prices = []          # stockage des ticks du cycle
trades = []          # historique des trades
open_buy = None
open_sell = None


async def handle_trades(bsm):
    global prices
    ts = bsm.trade_socket(SYMBOL.lower())
    await ts.__aenter__()  # start the socket
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
        await asyncio.sleep(CYCLE)

        if not prices:
            print(f"⚠️ Cycle vide | ticks=0")
            continue

        price_start = prices[0]
        price_end = prices[-1]
        min_price = min(prices)
        max_price = max(prices)
        ticks_count = len(prices)

        # Niveaux ordres
        buy_price = price_start * (1 - SPREAD)
        sell_price = price_start * (1 + SPREAD)
        spread_value = sell_price - buy_price
        spread_pct = SPREAD * 2 * 100

        # Placer les ordres si non existants
        open_buy = {"level": buy_price, "executed": False} if open_buy is None else open_buy
        open_sell = {"level": sell_price, "executed": False} if open_sell is None else open_sell

        # Ligne 1 : ordre positionné
        print(
            f"📝 Ordres positionnés price={price_start:.2f} | "
            f"BUY={open_buy['level']:.2f} SELL={open_sell['level']:.2f} "
            f"(spread={spread_value:.2f}, {spread_pct:.4f}%, ticks={ticks_count}, min={min_price:.2f}, max={max_price:.2f})"
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


async def main():
    client = await AsyncClient.create(API_KEY, API_SECRET)
    bsm = BinanceSocketManager(client)
    await asyncio.gather(handle_trades(bsm), strategy_loop())
    await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
