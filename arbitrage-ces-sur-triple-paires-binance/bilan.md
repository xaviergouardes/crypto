# Arbitrage sur Triplette sur le meme DEX Binance - via les api rest et le prix

## Conclusion
En conclusion va ne fonctionne pas : 
- les ordres sont passés avec des pris différents et sont donc décorrélé des signaux.
- Axe d'amélioration : utiliser le carnet d'order pour exploiter les prix ask et bid ainsi que les webscoket et un mécansime asynchrone.
- les frais ruines aussi les gains.

## Points sutrcturant de la solution
- récupéreation des prix via api rest et ticket // pas d'utilisation du carnet d'ordre
- ordre chainées les un derrire les autres de manière sequentielle.

## Résultat obtenus sur testnet.
toDO