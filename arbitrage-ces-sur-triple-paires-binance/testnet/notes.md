# API Binance 

https://testnet.binance.vision/

# HMAC-SHA-256 Key registered
Save these values right now. They won't be shown ever again!

API Key: 0Yg2BuETKk66Q8BlBeaFMw0KsNfhcrAvAHOUepJnIspeOk6Y1aUD7AK3I5G5VzR4

Secret Key: AjQJY88xbhXboTGgJfpX29DME5skYy5X8wmsYWSbwjeHdGZHfTR7dmxkGBJtxbJc

# les Etapes 
Étapes :

Aller sur le site du testnet Binance Spot :
👉 https://testnet.binance.vision/

Créer un compte (c’est gratuit, pas besoin d’un compte Binance normal).

Tu peux te connecter avec un compte GitHub ou un compte Google.

Une fois connecté, tu arrives sur ton dashboard.

Générer une clé API :

Dans ton tableau de bord, tu as une section API Key.

Clique sur Generate HMAC_SHA256 Key.

Tu obtiendras deux informations :

API_KEY

API_SECRET

Utiliser ces clés dans ton script :
Exemple :

API_KEY = "ta_cle_api_testnet"
API_SECRET = "ton_secret_testnet"


Changer l’URL de connexion :
Avec la librairie python-binance, il faut préciser que tu es sur le testnet :

from binance.client import Client

API_KEY = "ta_cle_api_testnet"
API_SECRET = "ton_secret_testnet"

client = Client(API_KEY, API_SECRET, testnet=True)


👉 Attention : l’URL par défaut de python-binance n’est pas toujours configurée pour le testnet.
Si besoin, tu peux forcer :

client.API_URL = 'https://testnet.binance.vision/api'