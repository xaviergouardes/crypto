import os
import time
import threading
from binance.client import Client
from decimal import Decimal, ROUND_DOWN

# 🔑 Clés API depuis variables d'environnement
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    raise Exception("Clés API manquantes !")

client = Client(API_KEY, API_SECRET, testnet=True)

symbol = "BTCUSDC"
quantity_usdc = 10        # montant max par ordre
spread = 0.002            # écart relatif pour BUY/SELL
delay = 5                 # secondes entre chaque cycle

# 🔹 Infos symbol pour les filtres
symbol_info = client.get_symbol_info(symbol)
lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
price_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')

min_qty = float(lot_size_filter['minQty'])
step_size = float(lot_size_filter['stepSize'])
tick_size = float(price_filter['tickSize'])

def round_step(value, step):
    step_dec = Decimal(str(step))
    value_dec = Decimal(str(value))
    rounded = (value_dec // step_dec) * step_dec
    return float(rounded)

def usdc_to_qty(usdc_amount, price):
    qty = usdc_amount / price
    qty = max(min_qty, round_step(qty, step_size))
    qty_str = str(Decimal(str(qty)).quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))
    return qty_str

# 🔹 Variables partagées
current_buy_order = None
current_sell_order = None
orders_lock = threading.Lock()
realized_pnl = 0.0
running = True

def monitor_orders():
    global realized_pnl, current_buy_order, current_sell_order
    while running:
        with orders_lock:
            for order, side_var in [(current_buy_order, 'BUY'), (current_sell_order, 'SELL')]:
                if order is None:
                    continue
                try:
                    status = client.get_order(symbol=symbol, orderId=order['orderId'])
                    if status['status'] == 'FILLED':
                        executed_qty = sum([float(f['qty']) for f in status['fills']])
                        executed_price = sum([float(f['price']) * float(f['qty']) for f in status['fills']]) / executed_qty
                        side = order['side']
                        print(f"✨ {side} exécuté : {executed_qty} BTC à {round(executed_price,2)} USDC")

                        if side == 'SELL' and current_buy_order:
                            realized_pnl += (executed_price - float(current_buy_order['price'])) * executed_qty

                        # Supprimer l'ordre exécuté pour ne pas le traiter à nouveau
                        if side == 'BUY':
                            current_buy_order = None
                        else:
                            current_sell_order = None

                except Exception as e:
                    pass
        time.sleep(1)

# 🔹 Lancer le thread de surveillance
thread = threading.Thread(target=monitor_orders, daemon=True)
thread.start()

print("🚀 Bot market making Mainnet safe - BTC/USDC - 1 paire d'ordre à la fois")

try:
    while True:
        ticker = client.get_symbol_ticker(symbol=symbol)
        price = float(ticker['price'])
        qty = usdc_to_qty(quantity_usdc, price)

        with orders_lock:
            # Annuler les anciens ordres
            if current_buy_order:
                try: client.cancel_order(symbol=symbol, orderId=current_buy_order['orderId'])
                except: pass
            if current_sell_order:
                try: client.cancel_order(symbol=symbol, orderId=current_sell_order['orderId'])
                except: pass

            # Calculer prix des nouveaux ordres
            buy_price = Decimal(str(price * (1 - spread))).quantize(Decimal(str(tick_size)), rounding=ROUND_DOWN)
            sell_price = Decimal(str(price * (1 + spread))).quantize(Decimal(str(tick_size)), rounding=ROUND_DOWN)

            # Passer nouveaux ordres
            current_buy_order = client.order_limit_buy(symbol=symbol, quantity=qty, price=str(buy_price))
            current_sell_order = client.order_limit_sell(symbol=symbol, quantity=qty, price=str(sell_price))

            print(f"🟢 BUY {qty} BTC à {buy_price} USDC | OrderID: {current_buy_order['orderId']}")
            print(f"🔴 SELL {qty} BTC à {sell_price} USDC | OrderID: {current_sell_order['orderId']}")
            print(f"💰 PnL réalisé : {round(realized_pnl,2)} USDC")

        time.sleep(delay)

except KeyboardInterrupt:
    print("\n🛑 Arrêt du bot détecté, annulation des ordres ouverts...")
    running = False
    thread.join()
    with orders_lock:
        if current_buy_order:
            try: client.cancel_order(symbol=symbol, orderId=current_buy_order['orderId'])
            except: pass
        if current_sell_order:
            try: client.cancel_order(symbol=symbol, orderId=current_sell_order['orderId'])
            except: pass
    print("✅ Tous les ordres annulés. Bot stoppé proprement.")
