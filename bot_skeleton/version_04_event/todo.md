
# Todo : 
- Travailler avec de timeframe différent. Pas exemple stratégie de MM sur 3 échelle de temps
- Réflechir si on ne pourrait pas simplifier la gestion des events  au sein du pipeline - il n'y aurait que le système qui ecoute des events tick candle et ensuite qu passe la dernière chandelle à tous les composants du pipeline pour qu'ils se mettent a jour. => plus event inter composant.
- Faire un Front VUEJS por piloter les Bots
- Lancer les bt et train en mode asynchrone et vernir récupérer le dernier résultat via un autre endpoint ``` /last_backtest ou last_trainnig ```
- Lancer le bt et train dans un vrai thread
- Vérifier que le TradeList en sortie du calcul des stats a un vrai interet ?
- Rennomer EventBus en BotEventBus -> en efftet il s'agit d'un bus onterne au bot + etudier la question d'injecter le bot dasn tous ses composants.
- BUG : L'arret du Bot en mode BackTest ne fonctionne pas
- BUG : Telegram notifier -> fermer proprement la connexion http -> je pense avec un Statable
- Faire une EMA with Buffer
- Synchroniser les event avec la candle partout
- Faire un test avec double calcul pandas et mon indicateur pour valider le croiseement RSI
- Faire un backtest non pas avec un fichier mais avec un appel api Binace sur 2 mois
- Réflechir a la réunification de system et signal engine dans le package bot cat il sont très liée 1 bot = 1 systeme = 1 signal engine
- Est-ce que ca a un sens de faire des bot avec du paramétrage plutot que du code : BotAbstrait + bot concret avec une surcharge des méthodes spécifiques ??? à réfléchir.
- BUG : le RSI n'est pas correctement initialisé, mais il se stablise après quelque jours.


# Doing : 
- Dans le RSICrossSignalEngine => prendre la notion de surcaht dasn l'indicateur et ne pas la mettre en dur < 70
- Vérifier aussi les calculs des trades ils me semble louche -> total profit

# Done : 
- Vérifier les signaux proposé par le cross RSI, ca me parait bizarre
- Faire juste un ifltre pour le moment, pas de multi filtrer dnas le pipline de trading -> plutot avec un argument dans l'event Trade Detect
- Premier Filtre ATR pour détecter les zone d'accumulation et les prémices d'une phase d'expansion
- Indicateurs ATR avec detection des phase accumulation et expansion
--> Ajouter un filter=on/off dans le RiskManager
--> Ajouter un filtred dans l'event : TradeSignalGenerated
- refactor du __init__.py pour faire un fichier par bot
- Dans les stats indiuer la date de début du bot et/ou  la durée execution
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