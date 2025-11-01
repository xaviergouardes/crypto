from datetime import datetime
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, CandleClose, PriceUpdated


class StrategySimpleSweepSwingEngine:
    """
    Stratégie Sweep Swing compatible avec IndicatorSimpleSwingDetector :
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        # Données courantes
        self.entry_price = None
        self.candle = None
        self.last_swing_high = None
        self.last_swing_low = None

        # Abonnements
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)

    async def on_price_update(self, event: PriceUpdated):
        self.entry_price = event.price

    async def on_indicator_update(self, event: IndicatorUpdated):
        """Récupère les swings forts émis par l'indicateur. IndicatorSimpleSwingDetector"""
        event_type = event.values.get("type")
        if event_type not in ("IndicatorSimpleSwingDetector",):
            return
        
        self.last_swing_high = event.values["last_swing_high"]
        self.last_swing_low = event.values["last_swing_low"]

        
    async def on_candle_close(self, event: CandleClose):
        """Chaque clôture de bougie déclenche une évaluation de la stratégie."""
        self.candle = event.candle
        await self.evaluate_strategy()

    async def evaluate_strategy(self):

        if not self.last_swing_low or not self.last_swing_high:
            return
        
        o, c, h, l = self.candle.open, self.candle.close, self.candle.high, self.candle.low
        bullish = c > o
        bearish = c < o

        # Calcul des mèches
        total_size = h - l
        if total_size == 0:
            return
        upper_wick = h - max(c, o)
        lower_wick = min(c, o) - l

        bearish_wick = upper_wick >= total_size / 3
        bullish_wick = lower_wick >= total_size / 3

        # Détection des sweeps
        last_swing_high_price = self.last_swing_high.high
        last_swing_low_price = self.last_swing_low.low
        sweep_high = bearish and o < last_swing_high_price < h 
        sweep_low = bullish and l < last_swing_low_price < o

        signal = None
        if sweep_high and bearish_wick:
            signal = "SELL"
        elif sweep_low and bullish_wick:
            signal = "BUY"

        if not signal:
            return

        # Log clair
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySimpleSweepSwingEngine] "
        #       f"Signal {signal} | candle={self.candle} | "
        #       f"swing high={self.last_swing_high} | "
        #       f"swing  low={self.last_swing_low}"
        # )

        # Publication du signal
        await self.event_bus.publish(TradeSignalGenerated(
            side=signal,
            confidence=1.0,
            price=self.entry_price,
            strategie = self.__class__.__name__,
            strategie_parameters = None,
            strategie_values = {
                "sweep_high": sweep_high,
                "sweep_low": sweep_low,
                "bearish_wick": bearish_wick,
                "bullish_wick": bullish_wick,
                "candle": self.candle,
                "last_swing_high": self.last_swing_high,
                "last_swing_low": self.last_swing_low,
            },
        ))


    async def run(self):
        pass
