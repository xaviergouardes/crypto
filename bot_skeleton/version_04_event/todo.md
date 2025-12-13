
# Todo : 
- Travailler avec de timeframe différent. Pas exemple stratégie de MM sur 3 échelle de temps
- Réflechir si on ne pourrait pas simplifier la gestion des events  au sein du pipeline - il n'y aurait que le système qui ecoute des events tick candle et ensuite qu passe la dernière chandelle à tous les composants du pipeline pour qu'ils se mettent a jour. => plus event inter composant.
- Faire un Front VUEJS por piloter les Bots
- Faire un backtest non pas avec un fichier mais avec un appel api Binace sur 2 mois
- Lancer les bt et train en mode asynchrone et vernir récupérer le dernier résultat via un autre endpoint ``` /last_backtest ou last_trainnig ```
- Lancer le bt et train dans un vrai thread
- Vérifier que le TradeList en sortie du calcul des stats a un vrai interet ?
- Rennomer EventBus en BotEventBus -> en efftet il s'agit d'un bus onterne au bot + etudier la question d'injecter le bot dasn tous ses composants.
- BUG : L'arret du Bot en mode BackTest ne fonctionne pas
- BUG : Telegram notifier -> fermer proprement la connexion http -> je pense avec un Statable
- Voir comment faire pour mettre des filtres optionnels dnas le pipline de trading -> prevoir des event spéciaux
- Dans les stats indiuer la date de début du bot et/ou  la durée execution
- Faire une EMA with Buffer
- Synchroniser les event avec la candle partout

# Doing : 
- Faire un test avec double calcul pandas et mon indicateur pour valider le croiseement RSI

# Done : 
- retirer le Price de partout et ajouter une cancdle dans tous les events
- retirer le price du TradeSignalGenerated
- Faire un indicateur RSI pour la stratégie double RSI
- Faire une acrchi plus prorpo pour les indicaterus dissociant l'indicateur et les event
- Ajouter la candle dans l'event IndicatorUpdated => supprimer le candle close dans IndicatorEmaCrossDetector
- Tester le backtest du bot ma_cross -> il ne fait jamais aucun trade ?!?
- construction du ema_cross_detector - indicateur
- Mise au point d'un TU nominal pour l'indicateur
- Terminer les TU aux limite pour l'indicateur Moving Average
- Mettre en place de TU
- Mieux gérer les status du serveur http et du bot en retour des commande http
- Mieux structurer le classe bot_serveur_http
- Restrcutuer le ser http en externalisant l'implementation des commande dans des handler
- Positionner le niveau de Log a chaud quand le serveur http est lancé
- BUG : Pour le random bot le backtest renvoi un total profit démesuré 8000
- refactorer l'appel a l'engine Stat qui je pense devrait etre dans le bot uniquement avec une methode get_stats pour les distribuer.
- Faire le clair sur les bot_id et bot_class 
- Revoir du coup l'annuaire des bots pour que l'association soit bot_type <-> Classe du Système de Trading
    -> Retirer la calsse Système du paramètres de construction du Bot
- Faire une vraie Factory de Bot => Abandonné , pas nécéssaire
- BUG - Les paramétres par defaut sont dépendant des bot aussi !!!
- Faire un end point /info qui renvoi les paramétres (et les dernière stats)
- Tester avec  un autre bot = Randdom bot
- BUG : Avec le bot random , le tick des chandelle s'arrete après le premier trade finailiser et message telegram envoyé
- implémenter la methode /stop
- implémenter la méthode /start