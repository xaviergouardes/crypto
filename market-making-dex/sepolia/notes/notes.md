# Market Making sur SEpolia et Uniswap V2

Impossible de tester car il n'y a pas assez de transaction pour faire bouger le prix

Solutions possibles

Injecter toi-même des transactions

Générer artificiellement du flux en envoyant des swaps depuis un script de test.

Cela simule un marché actif → ton bot voit du “prix réel” et des ordres exécutés.

Fork local avec Hardhat/Ganache

Déployer un environnement complet avec des pools test et un flux de transactions simulé.

Tu peux contrôler les volumes et la fréquence des trades → tests beaucoup plus fiables.

Attendre un testnet plus actif ou mainnet “paper trading”

Sur Mainnet, utiliser la lecture de l’état réel (prix et volume) mais sans envoyer réellement d’ETH/USDC → ton bot simule les ordres pour tester la logique.