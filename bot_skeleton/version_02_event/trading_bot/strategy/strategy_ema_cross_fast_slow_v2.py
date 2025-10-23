from datetime import datetime
from zoneinfo import ZoneInfo

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, PriceUpdated


class StrategyEmaCrossFastSlowEngine:
    """
    Stratégie : génère un signal de trade à partir des événements 'ema_cross'
    émis par IndicatorEmaCrossDetector.
    """

    def __init__(
        self,
        event_bus: EventBus,
        periode_slow_ema: int = 25,
        periode_fast_ema: int = 9
    ):
        self.event_bus = event_bus
        self.periode_slow_ema = periode_slow_ema
        self.periode_fast_ema = periode_fast_ema

        self.entry_price = None
        self.last_signal = None  # Pour éviter de répéter le même signal

        # Abonnements aux événements
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossFastSlowEngine] Initisation avec periode_slow_ema={self.periode_slow_ema} / periode_fast_ema={self.periode_fast_ema} ") 


    async def on_price_update(self, event: PriceUpdated):
        """Met à jour le dernier prix connu."""
        self.entry_price = event.price

    async def on_indicator_update(self, event: IndicatorUpdated):
        """
        Réagit uniquement aux événements de type 'ema_cross' produits par IndicatorEmaCrossDetector.
        """
        if event.values.get("type") != "ema_cross":
            return

        cross = event.values.get("signal")
        if cross not in ("bullish", "bearish"):
            return

        # Filtrer par période pour ne traiter que le détecteur voulu
        fast_period = event.values.get("fast_period")
        slow_period = event.values.get("slow_period")
        if fast_period != self.periode_fast_ema or slow_period != self.periode_slow_ema:
            return

        if self.entry_price is None:
            return

        signal = "BUY" if cross == "bullish" else "SELL"

        # Évite de répéter le même signal consécutif
        if self.last_signal == signal:
            return

        self.last_signal = signal

        # event_time_str = (
        #     event.timestamp.replace(tzinfo=ZoneInfo("UTC"))
        #     .astimezone(ZoneInfo("Europe/Paris"))
        #     .strftime("%Y-%m-%d %H:%M:%S")
        # )

        # print(
        #     f"{datetime.now(ZoneInfo('Europe/Paris')).strftime('%Y-%m-%d %H:%M:%S')} "
        #     f"[StrategyEmaCrossFastSlowEngine] 🔔 Signal détecté : {signal} "
        #     f"(time={event_time_str}, fast={fast_period}, slow={slow_period})"
        # )

        # Publier le signal de trade
        await self.event_bus.publish(
            TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                price=self.entry_price,
                strategie=self.__class__.__name__,
                strategie_parameters={
                    "periode_fast_ema": self.periode_fast_ema,
                    "periode_slow_ema": self.periode_slow_ema,
                },
                strategie_values={
                    "cross_signal": cross,
                },
            )
        )

    async def run(self):
        """Tout est événementiel."""
        pass
