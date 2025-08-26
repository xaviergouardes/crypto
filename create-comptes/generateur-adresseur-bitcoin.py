#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, hmac, hashlib, struct, secrets
import ecdsa
from mnemonic import Mnemonic
import bech32

# =========================
# Utils encodage / checksum
# =========================
_ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def b58encode(b: bytes) -> bytes:
    # Encodage Base58 (sans check)
    n = int.from_bytes(b, 'big')
    res = bytearray()
    while n > 0:
        n, r = divmod(n, 58)
        res.append(_ALPHABET[r])
    # Ajouter les '1' pour chaque 0x00 en tête
    pad = 0
    for c in b:
        if c == 0:
            pad += 1
        else:
            break
    return b'1' * pad + res[::-1]

def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def ripemd160(b: bytes) -> bytes:
    h = hashlib.new('ripemd160')
    h.update(b)
    return h.digest()

def hash160(b: bytes) -> bytes:
    return ripemd160(sha256(b))

def hmac_sha512(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha512).digest()

def ser32(i: int) -> bytes:
    return struct.pack('>L', i)

def ser256(p: int) -> bytes:
    return p.to_bytes(32, 'big')

def parse256(b: bytes) -> int:
    return int.from_bytes(b, 'big')

# =========================
# Courbe secp256k1
# =========================
curve = ecdsa.SECP256k1
G = curve.generator
order = curve.order

def privkey_to_pubkey_compressed(k_int: int) -> bytes:
    # Multiplication scalaire pour obtenir la clé publique
    pk_point = k_int * G
    x = pk_point.x()
    y = pk_point.y()
    return (b'\x02' if (y % 2 == 0) else b'\x03') + x.to_bytes(32, 'big')

# =========================
# BIP32: seed -> master -> child (CKD)
# =========================
def master_key_from_seed(seed: bytes):
    I = hmac_sha512(b"Bitcoin seed", seed)
    IL, IR = I[:32], I[32:]
    k = parse256(IL)
    if k == 0 or k >= order:
        raise ValueError("Master key dérivée invalide")
    return k, IR  # private key int, chain code

def ckd_priv(k_par: int, c_par: bytes, i: int):
    """Child Key Derivation (private) – BIP32.
       i >= 0x80000000 : dérivation durcie (hardened)
       i <  0x80000000 : dérivation normale
    """
    if i >= 0x80000000:
        # Hardened: 0x00 || ser256(k_par) || ser32(i)
        data = b'\x00' + ser256(k_par) + ser32(i)
    else:
        # Normal: ser_pub(parent) || ser32(i)
        data = privkey_to_pubkey_compressed(k_par) + ser32(i)
    I = hmac_sha512(c_par, data)
    IL, IR = I[:32], I[32:]
    ki = (parse256(IL) + k_par) % order
    if parse256(IL) >= order or ki == 0:
        # Très rare ; en pratique, on incrémente i et on recommence.
        raise ValueError("Child key invalide, réessayer avec un autre index")
    return ki, IR

# =========================
# WIF (Wallet Import Format)
# =========================
def privkey_to_wif(k_int: int, compressed: bool = True, mainnet: bool = True) -> str:
    # Préfixe: 0x80 mainnet ; 0xEF testnet
    prefix = b'\x80' if mainnet else b'\xEF'
    payload = prefix + ser256(k_int) + (b'\x01' if compressed else b'')
    chk = sha256(sha256(payload))[:4]
    return b58encode(payload + chk).decode()

# =========================
# Bech32 P2WPKH (BIP173) – adresse bc1...
# =========================
def pubkey_to_bech32_p2wpkh(pubkey_compressed: bytes, hrp: str = "bc") -> str:
    # P2WPKH witness program = RIPEMD160(SHA256(pubkey))
    witprog = hash160(pubkey_compressed)
    # witver = 0 pour P2WPKH
    return bech32.encode(hrp, 0, witprog)

# =========================
# Dérivation BIP84 (m/84'/0'/0'/0/0)
# =========================
def derive_bip84_account0_first_addr(k_master: int, c_master: bytes, coin_type_mainnet=True):
    # m / 84' / 0' / 0' / 0 / 0
    HARD = 0x80000000
    purpose = 84 | HARD
    coin    = (0 if coin_type_mainnet else 1) | HARD  # 0' = mainnet, 1' = testnet
    account = 0 | HARD
    change  = 0
    index   = 0

    k1, c1 = ckd_priv(k_master, c_master, purpose)
    k2, c2 = ckd_priv(k1, c1, coin)
    k3, c3 = ckd_priv(k2, c2, account)
    k4, c4 = ckd_priv(k3, c3, change)
    k5, c5 = ckd_priv(k4, c4, index)
    return k5, c5

# =========================
# MAIN
# =========================
def main():
    # 1) Mnémonique 24 mots (anglais)
    mnemo = Mnemonic("english")
    entropy = secrets.token_bytes(32)  # 256 bits -> 24 mots
    mnemonic_phrase = mnemo.to_mnemonic(entropy)

    # 2) Passphrase optionnelle (BIP39)
    try:
        passphrase = input("Entrez une passphrase (BIP39) facultative (laisser vide si aucune) : ")
    except EOFError:
        passphrase = ""

    # 3) Seed BIP39
    seed = mnemo.to_seed(mnemonic_phrase, passphrase)

    # 4) Master key BIP32
    k_master, c_master = master_key_from_seed(seed)

    # 5) Dérive clé privée enfant m/84'/0'/0'/0/0 (mainnet)
    k_child, c_child = derive_bip84_account0_first_addr(k_master, c_master, coin_type_mainnet=True)

    # 6) Clé publique compressée
    pubkey_compressed = privkey_to_pubkey_compressed(k_child)

    # 7) Adresse Bech32 (bc1...) P2WPKH
    address = pubkey_to_bech32_p2wpkh(pubkey_compressed, hrp="bc")

    # 8) WIF (compressé)
    wif = privkey_to_wif(k_child, compressed=True, mainnet=True)

    # 9) Affichage
    print("\n================= Bitcoin HD Wallet (BIP84) =================")
    print("Mnemonic (24 mots, anglais) :")
    print(mnemonic_phrase)
    print("\nPassphrase BIP39 :", "(aucune)" if passphrase == "" else passphrase)
    print("\nChemin de dérivation :", "m/84'/0'/0'/0/0 (P2WPKH mainnet)")
    print("Clé privée (hex) => import Binance KO :", ser256(k_child).hex())
    print("Clé privée (WIF, compressée) => import Binance OK  - native segwit :", wif)
    print("Clé publique compressée (hex) :", pubkey_compressed.hex())
    print("Adresse Bitcoin (Bech32) :", address)
    print("==============================================================\n")

if __name__ == "__main__":
    main()
