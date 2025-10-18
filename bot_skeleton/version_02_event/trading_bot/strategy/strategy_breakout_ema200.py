from datetime import datetime, timedelta
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import (
    CandleClose,
    PriceUpdated,
    TradeSignalGenerated,
    IndicatorUpdated
)

class StrategyBreakoutEMA200:
    """
    Stratégie simple de breakout EMA200 filtrée par ATR, volume et swings forts.

    Principe :
        - Signal d'achat si le prix casse l'EMA200 à la hausse avec un swing low récent.
        - Signal de vente si le prix casse l'EMA200 à la baisse avec un swing high récent.
        - Les breakouts doivent dépasser un multiple d'ATR et être soutenus par un volume supérieur à la moyenne.
        - atr_multiple doit etre supérieur a 1 , peut aller jusqu'a 2
        - Confirmation finale uniquement si le prix sort de la bande autour de l'EMA200
    """

    def __init__(self, event_bus: EventBus, atr_multiple: float = 1.0):
        self.event_bus = event_bus
        self.atr_multiple = atr_multiple

        self.entry_price = None
        self.ema200 = None
        self.atr = None
        self.avg_volume = None
        self.last_strong_swings = []

        self.candle = None
        self.symbol = None

        # Flags pour vérifier la réception des indicateurs
        self.received_ema200 = False
        self.received_atr = False
        self.received_avg_volume = False
        self.received_strong_swings = False

        # Signal potentiel en attente de confirmation
        self.pending_signal = None

        # Souscriptions
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)

    async def on_price_update(self, event: PriceUpdated):
        self.entry_price = event.price
        # La confirmation finale sera gérée dans evaluate_strategy()
        await self.evaluate_strategy()

    async def on_candle_close(self, event: CandleClose):
        self.candle = event.candle
        self.symbol = event.symbol.upper()
        await self.evaluate_strategy()

    async def on_indicator_update(self, event: IndicatorUpdated):
        # EMA 200
        if "ema_candle" in event.values and "ema_candle_period" in event.values:
            if event.values["ema_candle_period"] == 200:
                self.ema200 = event.values["ema_candle"]
                self.received_ema200 = True
            else:
                raise ValueError(
                    f"[StrategyBreakoutEMA] EMA reçue avec une période non supportée : {event.values['ema_candle_period']}"
                )

        # ATR
        if "atr" in event.values:
            self.atr = event.values["atr"]
            self.received_atr = True

        # Volume moyen
        if "avg_volume" in event.values:
            self.avg_volume = event.values["avg_volume"]
            self.received_avg_volume = True

        # Swings forts
        if "strong_swings" in event.values:
            self.last_strong_swings = event.values["strong_swings"]
            self.received_strong_swings = True

    def indicators_ready(self):
        """Retourne True si tous les indicateurs nécessaires ont été reçus."""
        return (
            self.received_ema200
            and self.received_atr
            and self.received_avg_volume
            and self.received_strong_swings
        )

    def price_out_of_ema_band(self, price: float) -> bool:
        """Retourne True si le prix sort de la bande autour de l'EMA200."""
        if not (self.ema200 and self.atr):
            return False
        upper_band = self.ema200 + self.atr * self.atr_multiple
        lower_band = self.ema200 - self.atr * self.atr_multiple
        return price > upper_band or price < lower_band

    async def evaluate_strategy(self):
        """Évalue la stratégie et gère à la fois le signal potentiel et la confirmation via la bande EMA200"""
        if not self.indicators_ready():
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyBreakoutEMA] "
                  f"Pas assez de données pour évaluer la stratégie "
                  f"atr={self.received_atr} "
                  f"avg_volume={self.received_avg_volume} "
                  f"strong_swings={self.received_strong_swings}")
            return

        if not self.candle or not self.entry_price:
            return

        o, c, h, l, vol = self.candle.open, self.candle.close, self.candle.high, self.candle.low, self.candle.volume

        # ---------------------------------------
        # Détection du signal potentiel
        # ---------------------------------------
        breakout_up = c > self.ema200 and (c - self.ema200) >= self.atr * self.atr_multiple and vol >= self.avg_volume
        breakout_down = c < self.ema200 and (self.ema200 - c) >= self.atr * self.atr_multiple and vol >= self.avg_volume

        signal = None

        if breakout_up:
            recent_low_swings = [s for s in self.last_strong_swings if s["type"] == "low"]
            if recent_low_swings and c >= recent_low_swings[-1]["price"]:
                signal = "BUY"
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyBreakoutEMA] Signal potentiel BUY détecté")
        elif breakout_down:
            recent_high_swings = [s for s in self.last_strong_swings if s["type"] == "high"]
            if recent_high_swings and c <= recent_high_swings[-1]["price"]:
                signal = "SELL"
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyBreakoutEMA] Signal potentiel SELL détecté")

        # ---------------------------------------
        # Mémorisation du signal potentiel
        # ---------------------------------------
        self.pending_signal = signal

        # ---------------------------------------
        # Confirmation du signal : prix sort de la bande
        # ---------------------------------------
        if self.pending_signal and self.price_out_of_ema_band(self.entry_price.price):
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyBreakoutEMA] "
                  f"Signal confirmé : {self.pending_signal} à prix {self.entry_price}")
            await self.event_bus.publish(
                TradeSignalGenerated(
                    side=self.pending_signal,
                    confidence=1.0,
                    price=self.entry_price
                )
            )
            self.pending_signal = None  # reset après confirmation

    async def run(self):
        pass
