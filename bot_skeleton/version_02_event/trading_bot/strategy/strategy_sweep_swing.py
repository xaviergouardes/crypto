from datetime import datetime

from collections import deque
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, CandleClose, PriceUpdated


class StrategySweepSwingEngine:
    """
    Stratégie : génère des signaux selon le croisement des prix avec l'EMA
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.entry_price = None
        self.swings = None
        self.candle = None
        self.last_swing_high = None
        self.last_swing_low = None
        self.last_swing_type = None

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
        self.entry_price = event.price.price
        self.received_price = True

    async def on_indicator_update(self, event: IndicatorUpdated):
        self.swings = event.values.get("swings")
        self.last_swing_high = event.values.get("last_swing_high")
        self.last_swing_low = event.values.get("last_swing_low")
        self.last_swing_type = event.values.get("last_swing_type")
        
        if self.last_swing_low is None or self.last_swing_high is None:
            self.received_indicator = False
            return
        
        self.received_indicator = True

    async def on_candle_close(self, event: CandleClose):
        self.candle = event.candle
        self.received_candle = True
        await self.evaluate_strategy()


    async def evaluate_strategy(self):
        #print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySweepSwingEngine] Evaluer la stratégie")

        # On ne calcule un signal que si tous les deux  événements ont été reçus au moins une fois
        if not (self.received_price and self.received_candle and self.received_indicator):
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySweepSwingEngine] Pas assez de données pour évaluer la stratégie")
            return

        signal = None

        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySweepSwingEngine] bullish={bullish} / bearish={bearish} / open={self.candle.open} / close={self.candle.close} / ema={self.ema}")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySweepSwingEngine] / "
              f"last_swing_high : {self.last_swing_high} / " 
              f"last_swing_low : {self.last_swing_low} / " 
              f"last_swing_type : {self.last_swing_type} / " 
              )

        # Conditions de signal

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

        bos_bullish = bullish and c > self.last_swing_high and self.last_swing_high > o
        # corps_au_dessus = (min(o, c) >= self.ema)

        bos_bearish = bearish and c < self.last_swing_low and self.last_swing_low < o
        # corps_en_dessous = (max(o, c) <= self.ema)

        sweep_last_swing_high = bearish and o < self.last_swing_high and h > self.last_swing_high
        sweep_last_swing_low = bullish and o > self.last_swing_low and l < self.last_swing_low

        # Conditions de signal
        if bos_bullish :
            signal = "BUY BOS"
        elif bos_bearish :
            signal = "SELL BOS"
        if sweep_last_swing_high :
            signal = "SELL SWEEP"
        elif sweep_last_swing_low :
            signal = "BUY WEEP"
        else:
            # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] Signal {signal} / {self.candle} / {self.ema}")
            return

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySweepSwingEngine] / "
              f"signal : {signal} / "
              f"candle : {self.candle} / " 
              )
        
        self.received_indicator = False
        self.received_candle = False
        self.received_price = False

    async def run(self):
        """Rien à faire ici : tout est événementiel."""
        pass
