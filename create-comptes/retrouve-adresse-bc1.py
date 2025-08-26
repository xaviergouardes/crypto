# pip install ecdsa base58 bech32
import hashlib
import ecdsa
import base58
from bech32 import bech32_encode, convertbits

def hex_to_wif(priv_hex, compressed=True):
    priv_bytes = bytes.fromhex(priv_hex)
    extended = b'\x80' + priv_bytes
    if compressed:
        extended += b'\x01'
    checksum = hashlib.sha256(hashlib.sha256(extended).digest()).digest()[:4]
    wif = base58.b58encode(extended + checksum).decode()
    return wif

def wif_to_priv_bytes(wif):
    decoded = base58.b58decode(wif)
    # retirer le prefix 0x80 et checksum (dernier 4 octets)
    priv = decoded[1:33]
    return priv

def priv_to_pub(priv_bytes):
    sk = ecdsa.SigningKey.from_string(priv_bytes, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    # clé compressée
    pub_bytes = b'\x02' + vk.to_string()[:32] if vk.to_string()[-1] % 2 == 0 else b'\x03' + vk.to_string()[:32]
    return pub_bytes

def pub_to_bech32(pub_bytes):
    # P2WPKH : hash160 de la clé publique
    sha256_pk = hashlib.sha256(pub_bytes).digest()
    ripemd160_pk = hashlib.new('ripemd160', sha256_pk).digest()
    # convertir en 5 bits
    converted = convertbits(ripemd160_pk, 8, 5)
    address = bech32_encode("bc", [0] + converted)
    return address

# ── INPUT ──
key_input = input("Entrez votre clé privée (hex ou WIF) : ").strip()

try:
    # déterminer si c'est hex ou WIF
    if len(key_input) == 64:  # hex brute
        priv_bytes = bytes.fromhex(key_input)
        wif_compressed = hex_to_wif(key_input, compressed=True)
        wif_uncompressed = hex_to_wif(key_input, compressed=False)
    else:
        wif_compressed = key_input
        wif_uncompressed = "N/A (input WIF existant)"
        priv_bytes = wif_to_priv_bytes(wif_compressed)

    pub_bytes = priv_to_pub(priv_bytes)
    address = pub_to_bech32(pub_bytes)

    print("\n===== Résultat =====")
    print("Clé privée WIF (compressée) :", wif_compressed)
    print("Clé privée WIF (non compressée) :", wif_uncompressed)
    print("Clé publique compressée (hex) :", pub_bytes.hex())
    print("Adresse Bitcoin Bech32 :", address)
    print("===================")

except Exception as e:
    print("Erreur :", e)
    print("→ Vérifie que la clé est bien une hex 64 caractères ou un WIF valide (51 ou 52 caractères).")
