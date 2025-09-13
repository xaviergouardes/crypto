# Arbitrage sur une tripleete de paire qur le meme DEX

## Points sutrcturant de la solution
- récupéreation des prix dans le carnet d'ordre : ask / bid
- véririfcation du volume au prix utilisé -> limiter le slipage
- utilisation des websocket plus rapide
- mécanisme asynchrone pour lire les prix en continue et les stocké dans un buffer.
- lexture du buffer périodiquement et execution des ordre sur la base de calcul des quantité préalable
- pas de chainage d'ordre
- optimisation pour réaliser le dernier ordre de vente après les autres et ainsi etre sur de récupérer la bonne quantité de ACH à vendre par exemple

## Conclusion 
- ça ne marche pas , les frais ruines les gains.

## Problèmes rencontrés : 
- ACHUSDC -> ACHBTC -> BTC USDC => fuite de BTC à chaque transaction je perds des BTC
    - raison : la quantité de BTC acheté et vendu n'est pas la meme
    - Solution : externaliser le dernier ordre de vente pour l'initialise avec la quantité acheté issue de l'ordre précedent.
    - Bilan : limite la fuite de BTC, mais on constate une fuite d'USDC que je n'explique pas vraiment. Peut-etre issue des frais.

