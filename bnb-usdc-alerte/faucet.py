import requests

# --- Adresse de ton compte BSC Testnet ---
wallet_address = "0x9e428f4042Be817983C2a810eDeA37CBa6aB940E"  # Remplace par ton adresse Testnet

# --- URL du faucet (BSC Testnet) ---
FAUCET_URL = "https://testnet.binance.org/faucet-smart"  # Site officiel

def request_tbnb(address):
    """Demande des tBNB sur le faucet Testnet"""
    try:
        # Certains faucets ne proposent pas d'API publique, donc ici on simule une requête POST
        # pour info : beaucoup nécessitent un captcha, impossible à automatiser sans le résoudre.
        response = requests.post(FAUCET_URL, data={"address": address})
        if response.status_code == 200:
            print(f"✅ tBNB demandé pour {address}")
        else:
            print(f"⚠ Erreur faucet {response.status_code} : {response.text}")
    except Exception as e:
        print("Erreur :", e)

if __name__ == "__main__":
    request_tbnb(wallet_address)
