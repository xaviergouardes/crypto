# Notes pour les expériences arbitrage ETH/USDC

## Infura

Sert à pouvoir executer des fonciton sur la block chain etherum sans avoir besoin de monter un noeud.

https://mainnet.infura.io/v3/3bdc55739dab4115ad4b202733a69938 

## clé api interscan sepolia
f76b0853152040bdae32cd27f82a2d8a

## env virtuel python
``
python3 -m venv venv

source venv/bin/activate
``

## Dépendance a installer
pip install pip install eth_account
pip install web3

## Pool HYPE
https://www.geckoterminal.com/hyperliquid/pools/0x13ba5fea7078ab3798fbce53b4d0721c?utm_source=chatgpt.com

## Sepolia
https://sepolia.dev/
explorateur de etherum testnet : https://goerli.etherscan.io?utm_source=chatgpt.com 

## Uniswap
explorateur uniswap sur telnet : https://app.uniswap.org/?utm_source=chatgpt.com#/swap?use=goerli

adresse de la factory de pool uniswap v3 sur sepolia : https://sepolia.etherscan.io/address/0x0227628f3F023bb0B980b67D528571c95c6DaC1c#events
=> aller voir dans les events les création de pool avec leur adresse et l'adresse des deux jetons.

## Nettoyer l'hitory de la console

```
history -c && history -w
```


# Commandes Unix pour screen

## Screen
Lister les screens : ```screen -list```
Créer un scréeen : ```screen -S toto```
Detacher un screens : ```Ctrl a + d```
Detacher un screens : ```Ctrl a + d```

## Lancer les robot en redirigant les logs
Lancer le robot : 
```python -u main04.py >> /home/bot-trading/20251023/logs/20251025_main04.log 2>&1 &```

Consulter les logs :
```tail - f /home/bot-trading/20251023/logs/20251025_main04.log```

Superviser le robot : 
```ps aux | grep python```

## Compresser et déployer les robots

```
tar -czvf 20251025_bot.tar.gz ./version_02_event

tar -xzvf 20251025_bot.tar.gz -C /chemin

```
