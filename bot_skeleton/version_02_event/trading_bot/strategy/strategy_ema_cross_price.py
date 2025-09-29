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
        self.ema = event.values.get("ema_candle")
        self.received_indicator = True

    async def on_candle_close(self, event: CandleClose):
        self.candle = event.candle
        self.received_candle = True
        await self.evaluate_strategy()


    async def evaluate_strategy(self):
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] Evaluer la stratégie")

        # On ne calcule un signal que si tous les deux  événements ont été reçus au moins une fois
        if not (self.received_price and self.received_candle and self.received_price):
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] Pas assez de données pour évaluer la stratégie")
            return

        signal = None

        # Déterminer le type de bougie
        bullish = self.candle.close > self.candle.open
        bearish = self.candle.close < self.candle.open
        
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossPriceEngine] bullish={bullish} / bearish={bearish} / open={self.candle.open} / close={self.candle.close} / ema={self.ema}")
        # Conditions de signal
        if bearish and self.candle.close < self.ema and self.ema < self.candle.open:
            signal = "SELL"
        elif bullish and self.candle.close > self.ema and self.ema > self.candle.open:
            signal = "BUY"
        else:
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
