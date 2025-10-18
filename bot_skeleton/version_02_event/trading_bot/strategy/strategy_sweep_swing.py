from datetime import datetime
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, CandleClose, PriceUpdated


class StrategySweepSwingEngine:
    """
    Stratégie Sweep Swing compatible avec IndicatorSwingDetector :
    ➤ Utilise les swings forts (strong_swings)
    ➤ Génère un signal BUY ou SELL selon le sweep du dernier swing fort
    ➤ Évite les signaux trop rapprochés via un espacement minimal
    """

    def __init__(self, event_bus: EventBus, min_swing_distance: int = 5, strength_threshold: float = 1.9):
        self.event_bus = event_bus
        self.min_swing_distance = min_swing_distance
        self.strength_threshold = strength_threshold

        # Données courantes
        self.entry_price = None
        self.candle = None
        self.strong_swings = []
        self.last_signal_index = None
        self.candle_index = 0

        # Abonnements
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)

    async def on_price_update(self, event: PriceUpdated):
        self.entry_price = event.price

    async def on_indicator_update(self, event: IndicatorUpdated):
        """Récupère les swings forts émis par l'indicateur."""
        swings = event.values.get("strong_swings", [])
        if not swings:
            return

        # On garde uniquement les swings très forts (≥ threshold)
        self.strong_swings = [
            s for s in swings if s["strength"] >= self.strength_threshold
        ]

    async def on_candle_close(self, event: CandleClose):
        """Chaque clôture de bougie déclenche une évaluation de la stratégie."""
        self.candle = event.candle
        self.candle_index += 1
        await self.evaluate_strategy()

    async def evaluate_strategy(self):
        if not self.strong_swings:
            return

        # Dernier swing fort connu
        last_swing = self.strong_swings[-1]
        swing_type = last_swing["type"]
        swing_price = last_swing["price"]
        swing_strength = last_swing["strength"]
        swing_index = last_swing["index"]

        # Vérifie l'espacement minimal avec le dernier signal
        if self.last_signal_index is not None:
            if self.candle_index - self.last_signal_index < self.min_swing_distance:
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
        sweep_high = swing_type == "high" and bearish and o < swing_price and h > swing_price
        sweep_low = swing_type == "low" and bullish and o > swing_price and l < swing_price

        signal = None
        if sweep_high and bearish_wick:
            signal = "SELL"
        elif sweep_low and bullish_wick:
            signal = "BUY"

        if not signal:
            return

        # Log clair
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategySweepSwingEngine] "
              f"Signal {signal} | strength={swing_strength:.2f} | type={swing_type} | "
              f"price={swing_price:.2f} | candle_index={self.candle_index}")

        # Publication du signal
        await self.event_bus.publish(TradeSignalGenerated(
            side=signal,
            confidence=1.0,
            price=self.entry_price
        ))

        # Marquer le dernier signal
        self.last_signal_index = self.candle_index

    async def run(self):
        pass
