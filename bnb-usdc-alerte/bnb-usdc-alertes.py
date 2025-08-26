import requests
import time

# --- Soldes initiaux ---
balance_usdc = 1000.0
balance_wusdc = 0.0
balance_wbnb = 0.0

# --- Paramètres ---
spread_threshold = 0.005  # 0.5%
trade_amount_usdc = 100   # montant simulé par trade

# --- Fonctions ---
def get_binance_price():
    """Prix BNB/USDC sur Binance"""
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDC").json()
        return float(r.get("price", 0))
    except:
        return 0

def get_pancakeswap_price():
    """
    Prix WBNB/WUSDC simulé sur PancakeSwap
    (remplacer par un call TheGraph ou Router pour live)
    """
    try:
        # Simulation : on applique un léger décalage aléatoire autour du prix Binance
        binance_price = get_binance_price()
        if binance_price == 0:
            return None
        # Simule une différence de ±0.5% pour test
        import random
        delta = random.uniform(-0.005, 0.005)
        return binance_price * (1 + delta)
    except:
        return None

def get_usdc_eur():
    """Approximation USD → EUR via USDT/EUR"""
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDT_EUR").json()
        price = r.get("price")
        return float(price) if price else 0.85
    except:
        return 0.85

# --- Affichage solde initial ---
usdc_eur = get_usdc_eur()
print(f"💰 Solde initial: {balance_usdc:.2f} USDC (~{balance_usdc*usdc_eur:.2f} EUR), "
      f"{balance_wbnb:.4f} WBNB, {balance_wusdc:.2f} WUSDC\n")

# --- Boucle principale ---
while True:
    try:
        binance_price = get_binance_price()
        pancake_price = get_pancakeswap_price()
        usdc_eur = get_usdc_eur()

        if binance_price == 0 or pancake_price is None:
            print("⚠ Impossible de récupérer les prix")
            time.sleep(10)
            continue

        spread = (binance_price - pancake_price) / pancake_price

        # Wrap automatique
        if balance_usdc > 0:
            balance_wusdc += balance_usdc
            balance_usdc = 0

        # Arbitrage : Binance > Pancake
        if spread > spread_threshold and balance_wusdc >= trade_amount_usdc:
            wbnb_bought = trade_amount_usdc / pancake_price
            balance_wusdc -= trade_amount_usdc
            balance_wbnb += wbnb_bought
            total_value = balance_wusdc + balance_wbnb * binance_price
            print(f"[ALERTE] Arbitrage 🚀")
            print(f"Acheter {wbnb_bought:.4f} WBNB sur PancakeSwap @ {pancake_price:.2f} WUSDC")
            print(f"Vendre sur Binance @ {binance_price:.2f} USDC")
            print(f"Solde: {balance_wusdc:.2f} WUSDC | {balance_wbnb:.4f} WBNB")
            print(f"Valeur totale ≈ {total_value:.2f} USDC (~{total_value*usdc_eur:.2f} EUR)\n")

        # Arbitrage inverse : Pancake > Binance
        elif spread < -spread_threshold and balance_wusdc >= trade_amount_usdc:
            wbnb_bought = trade_amount_usdc / binance_price
            balance_wusdc -= trade_amount_usdc
            balance_wbnb += wbnb_bought
            total_value = balance_wusdc + balance_wbnb * pancake_price
            print(f"[ALERTE] Arbitrage 🔄")
            print(f"Acheter {wbnb_bought:.4f} WBNB sur Binance @ {binance_price:.2f} USDC")
            print(f"Vendre sur PancakeSwap @ {pancake_price:.2f} WUSDC")
            print(f"Solde: {balance_wusdc:.2f} WUSDC | {balance_wbnb:.4f} WBNB")
            print(f"Valeur totale ≈ {total_value:.2f} USDC (~{total_value*usdc_eur:.2f} EUR)\n")

        time.sleep(10)

    except Exception as e:
        print("Erreur:", e)
        time.sleep(10)
