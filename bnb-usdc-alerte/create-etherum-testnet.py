#!/usr/bin/env python3
"""
gen_eth_account_simple.py
Génère une clé privée Ethereum et l'adresse correspondante.
Usage: python gen_eth_account_simple.py
"""

from eth_account import Account

def main():
    # Génération d'un compte Ethereum
    acct = Account.create()

    private_key_hex = acct.key.hex()   # clé privée en hex (0x...)
    address = acct.address             # adresse publique (0x...)

    print("=== Nouveau compte Ethereum (Testnet) ===")
    print(f"Adresse : {address}")
    print(f"Clé privée : {private_key_hex}")
    print()
    print("⚠️  Sauvegardez bien votre clé privée, elle permet de dépenser vos fonds.")
    print("Vous pouvez importer cette clé privée directement dans MetaMask ou tout autre wallet.")
    print()

if __name__ == "__main__":
    main()
