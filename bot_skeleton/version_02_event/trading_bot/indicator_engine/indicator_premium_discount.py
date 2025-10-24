from datetime import datetime
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import IndicatorUpdated, CandleClose

class IndicatorPremiumDiscount:
    """
    Détecte si le prix de clôture d'une bougie se situe dans une zone premium ou discount
    en fonction des swings high/low pertinents.
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.symbol = None

        self.max_swing_high = None
        self.min_swing_low = None

        # Souscription aux événements de swings et bougies closes
        self.event_bus.subscribe(IndicatorUpdated, self.on_swing_updated)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorPremiumDiscount] initialisé")

    async def on_swing_updated(self, event: IndicatorUpdated):
        """Récupère les derniers swings high et low pertinents."""
        type_event = event.values.get("type")
        
        # Ne traite que les events venant de IndicatorSimpleSwingDetector
        if type_event != "IndicatorSimpleSwingDetector":
            return

        self.symbol = event.symbol.upper()
        self.max_swing_high = event.values["max_swing_high"]["price"]
        self.min_swing_low = event.values["min_swing_low"]["price"]

    async def on_candle_close(self, event: CandleClose):
        """Détermine la zone premium/discount à la clôture de chaque bougie."""
        if event.symbol.upper() != self.symbol:
            return
        if self.max_swing_high is None or self.min_swing_low is None:
            return

        candle = event.candle
        zone = None

        mid_point = (self.max_swing_high + self.min_swing_low) / 2

        # Détermination de la zone selon la clôture et l'extrême de la bougie
        if candle.close >= mid_point:
            zone = "premium"
        else:
            zone = "discount"

        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                timestamp=candle.end_time,
                values={
                    "type": self.__class__.__name__,
                    "zone": zone,
                    "candle": candle,
                    "swing_high": self.max_swing_high,
                    "swing_low": self.min_swing_low,
                }
            )
        )

        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorPremiumDiscount] "
        #       f"zone: {zone} | close: {candle.close} | mid_point: {mid_point} | "
        #       f"max_swing_high: {self.max_swing_high} | min_swing_low: {self.min_swing_low}")

    async def run(self):
        pass