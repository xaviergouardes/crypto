from datetime import datetime
from zoneinfo import ZoneInfo

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, PriceUpdated


class StrategyEmaCrossFastSlowFilterPremDisEngine:
    """
    Stratégie : génère un signal de trade à partir des événements 'ema_cross'
    émis par IndicatorEmaCrossDetector, avec un filtre Premium/Discount.
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

        # Variables de contexte
        self.cross = None
        self.zone = None
        self.entry_price = None
        self.last_signal = None  # Évite la répétition de signaux identiques

        # Abonnement aux événements
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)

        now = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"{now} [StrategyEmaCrossFastSlowFilterPremDisEngine] Initialisation "
            f"(slow_ema={self.periode_slow_ema}, fast_ema={self.periode_fast_ema})"
        )

    async def on_price_update(self, event: PriceUpdated):
        """Met à jour le dernier prix connu."""
        self.entry_price = event.price

    async def on_indicator_update(self, event: IndicatorUpdated):
        """
        Réagit aux événements :
        - 'IndicatorEmaCrossDetector' : détection de croisement EMA
        - 'IndicatorPremiumDiscount' : mise à jour de la zone actuelle
        """
        event_type = event.values.get("type")
        if event_type not in ("IndicatorEmaCrossDetector", "IndicatorPremiumDiscount"):
            return

        if event_type == "IndicatorPremiumDiscount":
            self.zone = event.values.get("zone")
            return 

        if event_type == "IndicatorEmaCrossDetector":
            # Filtrer les périodes pour ne traiter que le détecteur voulu
            if (
                event.values.get("fast_period") != self.periode_fast_ema
                or event.values.get("slow_period") != self.periode_slow_ema
            ):
                return

            self.cross = event.values.get("signal")
            await self._evaluate_and_publish()

    async def _evaluate_and_publish(self):
        """
        Évalue la condition de trade et publie un signal si les critères sont remplis.
        """

        if not self.cross or not self.entry_price or not self.zone:
            # On attend d'avoir toutes les données nécessaires
            return

        cross = self.cross
        zone = self.zone
        signal = "BUY" if cross == "bullish" else "SELL"
        now = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")

        # --- Filtrage Premium / Discount ---
        if (signal == "BUY" and zone == "premium") or (signal == "SELL" and zone == "discount"):
            # print(
            #     f"{now} [StrategyEmaCrossFastSlowFilterPremDisEngine] ⚠️ Signal ignoré (filtré) : "
            #     f"{signal} en zone {zone} | cross={cross} "
            #     f"(fast={self.periode_fast_ema}, slow={self.periode_slow_ema})"
            # )
            return

        # --- Éviter la répétition de signaux identiques ---
        if signal == self.last_signal:
            return

        self.last_signal = signal

        # --- Log de validation ---
        # print(
        #     f"{now} [StrategyEmaCrossFastSlowFilterPremDisEngine] ✅ Signal détecté : "
        #     f"{signal} | zone={zone}, cross={cross} "
        #     f"(fast={self.periode_fast_ema}, slow={self.periode_slow_ema}) | "
        #     f"price={self.entry_price}"
        # )

        # --- Publication du signal de trade ---
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
                    "zone": zone,
                },
            )
        )

    async def run(self):
        """Boucle principale — tout est événementiel."""
        pass
