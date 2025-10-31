import time
import getpass
from xapi import xAPI


def main():
    # --- Connexion ---
    LOGIN = input("ID XTB : ")
    PASSWORD = getpass.getpass("Mot de passe : ")
    SERVER = "real"  # ou "real"

    client = xAPI(SERVER)
    client.login(LOGIN, PASSWORD)

    symbol = "EURUSD"
    print(f"Connexion réussie ✅ - Abonnement au flux {symbol} ...\n")

    # --- Callback exécuté à chaque tick ---
    def on_tick(data):
        if not data or "bid" not in data or "ask" not in data:
            return

        bid = data["bid"]
        ask = data["ask"]
        spread_pips = (ask - bid) * 1e5  # 1 pip = 0.00010
        mid = (bid + ask) / 2

        print(
            f"[{time.strftime('%H:%M:%S')}] "
            f"Bid: {bid:.5f} | Ask (prix d'achat): {ask:.5f} | "
            f"Spread: {spread_pips:.2f} pips | Mid: {mid:.5f}"
        )

    # --- Abonnement au flux temps réel ---
    client.stream.listenTicks(symbol, callback=on_tick)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du script par l'utilisateur...")

    # --- Nettoyage ---
    client.stream.stopListenTicks(symbol)
    client.logout()
    print("Déconnecté proprement 👋")


if __name__ == "__main__":
    main()
