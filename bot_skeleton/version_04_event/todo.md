
# Todo : 

- Je me demande si le Bot ne pourrais pas etre générique , il n'y a que son nom, id, port, et System de Trading qui sont spécialisé et les paramétres par défaut
- Lancer les bt et train en mode asynchrone et vernir récupérer le dernier résultat via un autre endpoint ``` /last_backtest ou last_trainnig ```
- Lancer le bt et train dans un vrai thread
- Positionner le niveau de Log a chaud quand le serveur http est lancé

- Mieux gérer les status du serveur http et du bot en retour des commande http
- BUG : Pour le random bot le backtest renvoi un total profit démesuré 8000


# Doing : 
- Faire un end point /info qui renvoi les paramétres (et les dernière stats)

# Done : 
- Tester avec  un autre bot = Randdom bot
- BUG : Avec le bot random , le tick des chandelle s'arrete après le premier trade finailiser et message telegram envoyé
- implémenter la methode /stop
- implémenter la méthode /start