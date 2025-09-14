import os
from binance.client import Client
import threading
import time

# 🔑 Clés API depuis variables d'environnement
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    raise Exception("Clés API manquantes ! Vérifie tes variables d'environnement.")

client = Client(API_KEY, API_SECRET, testnet=True)

# ⚙️ Paramètres
symbol = "BTCUSDT"
spread = 0.001       # écart par rapport au carnet (0.1%)
delay = 3            # secondes entre chaque update
quantity = 0.001     # quantité fixe par ordre

print("🚀 Bot Market Making avec une seule fourchette à la fois...")

# Soldes initiaux
balance_btc = float(client.get_asset_balance(asset="BTC")["free"])
balance_usdt = float(client.get_asset_balance(asset="USDT")["free"])
price_init = float(client.get_symbol_ticker(symbol=symbol)["price"])
btc_avg_price = price_init if balance_btc > 0 else 0.0
realized_pnl = 0.0

print(f"💰 Solde initial : {balance_btc:.6f} BTC, {balance_usdt:.2f} USDT")
print(f"Prix initial BTC : {price_init:.2f} USDT")

# 🟢 Thread pour tracer les trades exécutés de manière asynchrone
initial_trades = client.get_my_trades(symbol=symbol)
executed_trades = set(t['id'] for t in initial_trades)

def trace_trades():
    global executed_trades, realized_pnl, balance_btc, balance_usdt, btc_avg_price
    while True:
        try:
            trades = client.get_my_trades(symbol=symbol)
            for t in trades:
                trade_id = t['id']
                if trade_id not in executed_trades:
                    executed_trades.add(trade_id)
                    side = "🟢 ACHAT" if t['isBuyer'] else "🔴 VENTE"
                    qty = float(t['qty'])
                    price = float(t['price'])

                    if t['isBuyer']:
                        # Achat : mise à jour prix moyen et soldes
                        total_btc = balance_btc + qty
                        btc_avg_price = ((btc_avg_price * balance_btc) + (price * qty)) / total_btc if total_btc > 0 else price
                        balance_btc += qty
                        balance_usdt -= price * qty
                        pnl_trade = 0.0
                    else:
                        # Vente : mise à jour PnL et soldes
                        pnl_trade = qty * (price - btc_avg_price)
                        realized_pnl += pnl_trade
                        balance_btc -= qty
                        balance_usdt += price * qty

                    print(f"✨ [{side}] Executé : {qty} BTC à {price:.2f} USDT | PnL trade : {pnl_trade:.2f}")

        except Exception as e:
            print(f"⚠️ Erreur trace_trades : {e}")
        time.sleep(1)

threading.Thread(target=trace_trades, daemon=True).start()

try:
    while True:
        # 🔹 Lecture du carnet d'ordres
        order_book = client.get_order_book(symbol=symbol, limit=5)
        best_bid = float(order_book['bids'][0][0])
        best_ask = float(order_book['asks'][0][0])

        # Définition des prix d'achat et de vente (une seule fourchette)
        buy_price = round(best_bid * (1 - spread), 2)
        sell_price = round(best_ask * (1 + spread), 2)

        # Annule tous les ordres existants pour conserver une seule fourchette
        open_orders = client.get_open_orders(symbol=symbol)
        for o in open_orders:
            client.cancel_order(symbol=symbol, orderId=o["orderId"])

        # Placement de la paire d'ordres
        if balance_usdt >= buy_price * quantity:
            client.order_limit_buy(symbol=symbol, quantity=quantity, price=str(buy_price))
            print(f"🟢 Ordre d'achat placé à {buy_price} pour {quantity} BTC")

        if balance_btc >= quantity:
            client.order_limit_sell(symbol=symbol, quantity=quantity, price=str(sell_price))
            print(f"🔴 Ordre de vente placé à {sell_price} pour {quantity} BTC")

        # PnL non réalisé
        price = float(client.get_symbol_ticker(symbol=symbol)["price"])
        unrealized_pnl = balance_btc * (price - btc_avg_price)
        total_pnl = realized_pnl + unrealized_pnl
        total_value = balance_usdt + balance_btc * price

        print(f"Prix BTC: {price} | Portefeuille: {total_value:.2f} USDT | Réalisé: {realized_pnl:.2f} | Non réalisé: {unrealized_pnl:.2f} | Total PnL: {total_pnl:.2f}")

        time.sleep(delay)

except KeyboardInterrupt:
    print("\n🛑 Arrêt du bot détecté, annulation des ordres ouverts...")
    open_orders = client.get_open_orders(symbol=symbol)
    for o in open_orders:
        client.cancel_order(symbol=symbol, orderId=o["orderId"])
    print("✅ Tous les ordres annulés.")

    # Bilan final
    price = float(client.get_symbol_ticker(symbol=symbol)["price"])
    unrealized_pnl = balance_btc * (price - btc_avg_price)
    total_pnl = realized_pnl + unrealized_pnl
    total_value = balance_usdt + balance_btc * price
    print(f"💰 Bilan final : Portefeuille = {total_value:.2f} USDT | Réalisé: {realized_pnl:.2f} | Non réalisé: {unrealized_pnl:.2f} | Total PnL: {total_pnl:.2f}")
    print("Bot arrêté proprement.")
