
# Todo : 
- Faire un backtest non pas avec un fichier mais avec un appel api Binace sur 2 mois
- Lancer les bt et train en mode asynchrone et vernir récupérer le dernier résultat via un autre endpoint ``` /last_backtest ou last_trainnig ```
- Lancer le bt et train dans un vrai thread
- Positionner le niveau de Log a chaud quand le serveur http est lancé

- Mieux gérer les status du serveur http et du bot en retour des commande http
- BUG : Pour le random bot le backtest renvoi un total profit démesuré 8000
- refactorer l'appel a l'engine Stat qui je pense devrait etre dans le bot uniquement avec une methode get_stats pour les distribuer.

# Doing : 
- Première expérimentation avec un Bot Générique -> Faire une vraie Factory de Bot
- Revoir du coup l'annuaire des bots pour que l'association soit bot_type <-> Classe du Système de Trading
    -> Retirer la calsse Système du paramètres de construction du Bot
- Faire le clair sur les bot_id et bot_class 

# Done : 
- Faire un end point /info qui renvoi les paramétres (et les dernière stats)
- Tester avec  un autre bot = Randdom bot
- BUG : Avec le bot random , le tick des chandelle s'arrete après le premier trade finailiser et message telegram envoyé
- implémenter la methode /stop
- implémenter la méthode /start