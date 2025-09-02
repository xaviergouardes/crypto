#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binance.client import Client


client = Client(None, None)

# Récupérer toutes les paires actives
info = client.get_exchange_info()
all_symbols = [s['symbol'] for s in info['symbols'] if s['status'] == 'TRADING']

# Ne garder que les paires avec USDC
usdc_pairs = [s for s in all_symbols if 'USDC' in s]

# Construire un dictionnaire pour base et quote
pair_dict = {}
for s in all_symbols:
    # simple séparation base/quote
    if s.endswith('USDC'):
        pair_dict[s] = (s[:-4], 'USDC')
    elif s.startswith('USDC'):
        pair_dict[s] = ('USDC', s[4:])
    else:
        pair_dict[s] = (s[:-3], s[-3:])  # approximation pour autres paires

# Identifier les triplets
triplets = []
for pair1 in usdc_pairs:
    base1, quote1 = pair_dict[pair1]
    asset1 = quote1 if base1 == 'USDC' else base1

    for pair2 in all_symbols:
        if pair2 == pair1:
            continue
        base2, quote2 = pair_dict[pair2]
        if asset1 not in [base2, quote2]:
            continue
        asset2 = quote2 if base2 == asset1 else base2
        if asset2 == 'USDC':
            continue  # intermédiaire ne doit pas être USDC

        for pair3 in usdc_pairs:
            if pair3 in [pair1, pair2]:
                continue
            base3, quote3 = pair_dict[pair3]
            if asset2 not in [base3, quote3]:
                continue
            # retour à USDC
            if 'USDC' not in [base3, quote3]:
                continue

            triplets.append([pair1, pair2, pair3])

print(f"Nombre de triplets trouvés : {len(triplets)}")
#for t in triplets[:50]:
for t in triplets:
     print(t)
