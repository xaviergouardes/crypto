from datetime import datetime

from collections import deque
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, CandleClose, PriceUpdated


class StrategyEmaCrossPriceEngine:
    """
    Stratégie : génère des signaux selon le croisement des prix avec l'EMA
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.entry_price = None
        self.ema = None
        self.candle = None

        # Flags pour savoir si on a reçu au moins un événement de chaque type
        self.received_indicator = False
        self.received_candle = False
        self.received_price = False

        # Abonnement aux SMA des chandelles
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)

    async def on_price_update(self, event: PriceUpdated) -> None:
        """Réception d'un nouveau prix."""
        self.entry_price = event.price
        self.received_price = True

    async def on_indicator_update(self, event: IndicatorUpdated):
        ema_value = event.values.get("ema_candle")

        if ema_value is not None:
            self.ema = ema_value

        self.received_indicator = True

    async def on_candle_close(self, event: CandleClose):
        self.candle = event.candle
        self.received_candle = True
        await self.evaluate_strategy()


    async def evaluate_strategy(self):
        #print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] Evaluer la stratégie")

        # On ne calcule un signal que si tous les deux  événements ont été reçus au moins une fois
        if not (self.received_price and self.received_candle and self.received_indicator):
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] Pas assez de données pour évaluer la stratégie")
            return

        signal = None

        # Déterminer le type de bougie
        bullish = self.candle.close > self.candle.open
        bearish = self.candle.close < self.candle.open
        
        o, c = self.candle.open, self.candle.close
        h, l = self.candle.high, self.candle.low
        # c1, c2 = data[t-1]['close'], data[t-2]['close']
        # e, e1, e2 = ema[t], ema[t-1], ema[t-2]

        corps = abs(c - o)
        taille_bougie = h - l

        # Corps >= 2/3 de la bougie
        seuil_corps = 1/3
        grand_corps = taille_bougie > 0 and (corps >= seuil_corps * taille_bougie)

        # Calcul des mèches
        meche_haute = h - max(o, c)
        meche_basse = min(o, c) - l

        cross_up = self.candle.close > self.ema > self.candle.open
        # corps_au_dessus = (min(o, c) >= self.ema)

        cross_down = self.candle.close < self.ema < self.candle.open
        # corps_en_dessous = (max(o, c) <= self.ema)

        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] bullish={bullish} / bearish={bearish} / open={self.candle.open} / close={self.candle.close} / ema={self.ema}")
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] grand_corps {grand_corps} / "
        #       f"meche_haute {meche_haute} / "
        #       f"meche_basse {meche_basse} / "
        #       f"cross_up {cross_up} / "
        #       f"cross_down {cross_down}")
        # Conditions de signal
        if cross_down and (grand_corps and (meche_haute > meche_basse) ):
            signal = "SELL"
        elif cross_up and (grand_corps and (meche_basse > meche_haute) ):
            signal = "BUY"
        else:
            # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] Signal {signal} / {self.candle} / {self.ema}")
            return

        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] Signal {signal} / {self.candle} / {self.ema}")
        if signal:
            await self.event_bus.publish(TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                price=self.entry_price,  
            ))

        self.received_indicator = False
        self.received_candle = False
        self.received_price = False

    async def run(self):
        """Rien à faire ici : tout est événementiel."""
        pass
