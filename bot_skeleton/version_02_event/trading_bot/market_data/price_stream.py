import os
import asyncio
import aiohttp
import time
from datetime import datetime
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import PriceUpdated, Price

class PriceStream:
    def __init__(self, event_bus: EventBus, symbol: str = "ethusdc"):
        self.event_bus = event_bus
        self.symbol = symbol.lower()
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@trade"
        self.last_print_time = 0

    async def run(self):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [PriceStream] Démarrage du flux pour {self.symbol.upper()}")

        while True:  # ✅ Boucle infinie pour garder la connexion en vie
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self.ws_url, heartbeat=30) as ws:
                        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [PriceStream] Connecté à Binance WebSocket ({self.symbol.upper()})")

                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = msg.json()
                                price = float(data["p"])
                                volume = float(data["q"])

                                await self.event_bus.publish(
                                    PriceUpdated(
                                        Price(
                                            symbol=self.symbol.upper(),
                                            price=price,
                                            volume=volume,
                                            timestamp=datetime.now(),
                                        )
                                    )
                                )

                                now = time.time()
                                if now - self.last_print_time >= 60 * 15:
                                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [PriceStream] ({self.symbol.upper()}) 📈 Prix actuel : {price:.2f}")
                                    self.last_print_time = now

                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                print(f"[PriceStream] Erreur WebSocket ({self.symbol.upper()}), reconnexion dans 5s...")
                                break  # sort de la boucle async for

            except Exception as e:
                print(f"[PriceStream] Exception : {e.__class__.__name__} - {e}")
                print("[PriceStream] Tentative de reconnexion dans 10s...")
                await asyncio.sleep(10)
