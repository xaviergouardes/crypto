from typing import List, override
import pandas as pd
import requests
import json
import websockets
import asyncio
from datetime import datetime, timedelta
import pytz
import logging

from trading_bot.core.logger import Logger
from trading_bot.core.events import Candle, CandleHistoryReady, CandleClose
from trading_bot.market_data.candle_source import CandleSource
from trading_bot.core.event_bus import EventBus


class CandleSourceBinance(CandleSource):
    
    logger = Logger.get("CandleSourceBinance")

    def __init__(self, event_bus: EventBus, params: dict):
        super().__init__(event_bus)
        self.params = params

        self.symbol = params["symbol"]
        self.interval = params["interval"]
        self.warmup_count = params["trading_system"]["warmup_count"]

        self._ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{self.interval}"
        self._rest_url = f"https://api.binance.com/api/v3/klines?symbol={self.symbol.upper()}&interval={self.interval}&limit={self.warmup_count + 1}"
        self._reconnect_delay = 5  # secondes

        self._seconds = int(self.interval[:-1]) * 60  # intervalle en secondes

    @override
    async def _warmup(self):
        """
        Récupère les dernières bougies via l'API REST
        et publie un CandleHistoryReady.
        """
        try:
            resp = requests.get(self._rest_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            self.self.logger.error(f"Erreur récupération bougies via REST : {e}")
            return pd.DataFrame(columns=["timestamp", "timestamp_paris", "open", "high", "low", "close", "volume"])

        data = data[:-1]  # ignorer la dernière bougie potentiellement en cours

        candles = [self._dict_to_candle(k) for k in data[-self.warmup_count:]]

        self.logger.info(f"Warmup chargé ({len(candles)} bougies)")
        self.logger.info(f"Première bougie: {candles[0]}")
        self.logger.info(f"Dernière bougie: {candles[-1]}")

        await self.event_bus.publish(
            CandleHistoryReady(
                symbol=self.symbol,
                timestamp=datetime.now(),
                period=self.interval,
                candles=candles
            )
        )

    @override
    async def _stream(self):
        """
        Flux temps réel : publie un CandleClose pour chaque bougie clôturée.
        """
        while not self.should_stop():
            try:
                self.logger.info(f"Connexion au websocket Binance ({self.symbol}, {self.interval})...")
                async with websockets.connect(self._ws_url) as ws:
                    self.logger.info("✅ Connecté au websocket Binance")
                    async for message in ws:
                        data = json.loads(message)
                        k = data["k"]
                        if k["x"]:  # bougie clôturée
                            candle = self._ws_dict_to_candle(k)
                            self.logger.info(f"Bougie Close : {candle}")
                            await self.event_bus.publish(CandleClose(
                                symbol=self.symbol,
                                candle=candle
                            ))

            except websockets.ConnectionClosed as e:
                self.logger.warning(f"Websocket fermé : {e}. Reconnexion dans {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
            # except Exception as e:
            #     self.logger.error(f"Erreur websocket inattendue : {e}. Reconnexion dans {self._reconnect_delay}s...")
            #     await asyncio.sleep(self._reconnect_delay)

    # --- Méthodes utilitaires ---
    def _dict_to_candle(self, k) -> Candle:
        """Transforme une entrée REST en Candle."""
        ts_utc = pd.to_datetime(k[0], unit="ms", utc=True)
        return Candle(
            symbol=self.symbol,
            open=float(k[1]),
            high=float(k[2]),
            low=float(k[3]),
            close=float(k[4]),
            volume=float(k[5]),
            start_time=ts_utc,
            end_time=ts_utc + timedelta(seconds=self._seconds)
        )

    def _ws_dict_to_candle(self, k) -> Candle:
        """Transforme une entrée websocket en Candle."""
        ts_utc = datetime.fromtimestamp(k["t"] / 1000, tz=pytz.UTC)
        return Candle(
            symbol=self.symbol,
            open=float(k["o"]),
            high=float(k["h"]),
            low=float(k["l"]),
            close=float(k["c"]),
            volume=float(k["v"]),
            start_time=ts_utc,
            end_time=ts_utc + timedelta(seconds=self._seconds)
        )
