from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import Candle, TradeSignalGenerated, IndicatorUpdated

class PriceCrossEmaSignalEngine:

    _logger = Logger.get("PriceCrossEmaSignalEngine")

    def __init__(self, event_bus: EventBus, ema_period: int):
        self.event_bus = event_bus

        self.ema_period = ema_period
        self.ema_value = None
        self.ema_band_with = 0.008 # 0.001 = 0.1 %

        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)


    async def on_indicator_update(self, event: IndicatorUpdated):

        if event.values.get("type") != "MovingAverage":
            return
        period = event.values.get("ema_period")
        value = event.values.get("ema_value")

        if period is None or value is None:
            return
        
        if period == self.ema_period:
            self.ema_value = value     

        await self.evaluate_strategy(event.candle)


    async def evaluate_strategy(self, candle: Candle):
        if self.ema_value is None:
            return
        
        signal = None

        # Déterminer le type de bougie
        candle_bullish = candle.close > candle.open
        candle_bearish = candle.close < candle.open
        
        o, c = candle.open, candle.close
        h, l = candle.high, candle.low

        corps = abs(c - o)
        taille_bougie = h - l

        # Corps >= 2/3 de la bougie
        seuil_corps = 1/3
        grand_corps = taille_bougie > 0 and (corps >= seuil_corps * taille_bougie)

        # Calcul des mèches
        meche_haute = h - max(o, c)
        meche_basse = min(o, c) - l

        # marge relative autour de l'EMA (par exemple 0.1%)
        buffer = self.ema_value * self.ema_band_with  # 0.1% autour de l'EMA
        ema_high_band = self.ema_value + buffer
        ema_low_band = self.ema_value - buffer

        # Cassures
        cross_up = o < ema_high_band < c
        cross_down = c < ema_low_band < o

        if cross_down and (grand_corps and (meche_haute > meche_basse) ) and candle_bearish:
            signal = "SELL"
        elif cross_up and (grand_corps and (meche_basse > meche_haute) ) and candle_bullish:
            signal = "BUY"
        else:
            return

        self.last_signal = signal  
        self._logger.debug(f"signal={self.last_signal} [ EMA({self.ema_period })={self.ema_value:.2f}] | ema_band_with={self.ema_band_with}  | candle={candle}")
        await self._signal_emit(candle)  



    async def _signal_emit(self, candle: Candle):
        await self.event_bus.publish(TradeSignalGenerated(
                    side=self.last_signal,
                    confidence=1.0,
                    candle=candle,
                    strategie=self.__class__.__name__,
                    strategie_parameters={
                        "ema_period":self.ema_period,
                        "ema_band_with": self.ema_band_with
                    },
                    strategie_values={
                        "ema_value": self.ema_value,
                    },
                ))
