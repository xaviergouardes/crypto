import pandas as pd
import requests
import json
import websockets
import asyncio
from datetime import datetime
import pytz
from .candle_source import CandleSource
import logging

# Configuration du logger
logger = logging.getLogger("CandleSourceBinance")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Fuseau horaire Paris
PARIS_TZ = pytz.timezone("Europe/Paris")

class CandleSourceBinance(CandleSource):
    def __init__(self, symbol="ethusdc", interval="5m", warmup_count=50):
        self.symbol = symbol.lower()
        self.interval = interval
        self.warmup_count = warmup_count
        self._ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{self.interval}"
        self._rest_url = f"https://api.binance.com/api/v3/klines?symbol={self.symbol.upper()}&interval={self.interval}&limit={self.warmup_count + 1}"
        self._reconnect_delay = 5  # secondes avant tentative de reconnexion

    def get_initial_data(self) -> pd.DataFrame:
        """
        Récupère les dernières `warmup_count` bougies via l'API REST de Binance
        et ajoute la colonne `timestamp_paris`.
        On ignore la dernière bougie potentiellement incomplète pour éviter le recouvrement.
        """
        try:
            resp = requests.get(self._rest_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Erreur récupération bougies via REST : {e}")
            return pd.DataFrame(columns=["timestamp", "timestamp_paris", "open", "high", "low", "close", "volume"])

        # On prend tout sauf la dernière bougie (potentiellement en cours)
        data = data[:-1]

        rows = []
        for k in data[-self.warmup_count:]:  # on garde uniquement warmup_count bougies
            ts_utc = pd.to_datetime(k[0], unit="ms", utc=True)
            ts_paris = ts_utc.tz_convert(PARIS_TZ)
            rows.append({
                "timestamp": ts_utc,
                "timestamp_paris": ts_paris,
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            })
        df = pd.DataFrame(rows)
        logger.info(f"✅ {len(df)} bougies récupérées pour le warmup (sans recouvrement)")
        return df

    async def stream(self, on_new_candle):
        """
        Flux temps réel : déclenche `on_new_candle` pour chaque bougie clôturée.
        Gère les erreurs et tente une reconnexion automatique.
        """
        while True:
            try:
                logger.info(f"Connexion au websocket Binance ({self.symbol}, {self.interval})...")
                async with websockets.connect(self._ws_url) as ws:
                    logger.info("✅ Connecté au websocket Binance")
                    async for message in ws:
                        data = json.loads(message)
                        k = data["k"]
                        if k["x"]:  # bougie clôturée
                            ts_utc = datetime.fromtimestamp(k["t"]/1000, tz=pytz.UTC)
                            candle = {
                                "timestamp": ts_utc,
                                "timestamp_paris": ts_utc.astimezone(PARIS_TZ),
                                "open": float(k["o"]),
                                "high": float(k["h"]),
                                "low": float(k["l"]),
                                "close": float(k["c"]),
                                "volume": float(k["v"])
                            }
                            on_new_candle(candle)
            except websockets.ConnectionClosed as e:
                logger.warning(f"Websocket fermé : {e}. Reconnexion dans {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
            # except Exception as e:
            #     logger.error(f"Erreur websocket inattendue : {e}. Reconnexion dans {self._reconnect_delay}s...")
            #     await asyncio.sleep(self._reconnect_delay)
