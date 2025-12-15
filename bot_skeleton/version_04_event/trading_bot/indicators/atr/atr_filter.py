import copy
from datetime import datetime, timezone
from trading_bot.core.logger import Logger
from trading_bot.core.events import (
    IndicatorUpdated,
    TradeSignalGenerated
)
from trading_bot.core.event_bus import EventBus


class AtrFilter:
    """
    Wrapper EventBus autour de l'ATR Wilder.
    Sert de filtre de régime de marché (accumulation / expansion).
    """

    _logger = Logger.get("AtrFilter")

    def __init__(
        self,
        event_bus: EventBus
    ):
        self.event_bus = event_bus
        self.symbol: str | None = None

        self.market_phase = None
        self.last_market_phase_update = None

        event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)
        event_bus.subscribe(TradeSignalGenerated, self.on_trade_signal_generated)
 
        self._logger.info(f" Initilisé ")

    # ------------------------------------------------------------------
    # Temps réel
    # ------------------------------------------------------------------
    async def on_indicator_update(self, event: IndicatorUpdated):
        if event.values.get("type") != "Atr":
            return
        ts = datetime.now(timezone.utc)
        self.market_phase = event.values["market_phase"]
        self.last_market_phase_update = ts

    async def on_trade_signal_generated(self, event: TradeSignalGenerated):
        
        # Ne pas traiter les event qui ont déjà été trité par moi-meme
        if event.filtred:
            return

        # vérifier que l'écart de temps entres les deux events soit inférieur à la seconde.
        tolerance_sec = 1.0 # une seconde max d'écart
        ts = datetime.now(timezone.utc)
        ecart  = abs((self.last_market_phase_update - ts).total_seconds()) <= tolerance_sec
        if not ecart:
            return
        
        if self.market_phase == "expansion":
            event_filtered = copy.deepcopy(event)
            event_filtered.mark_filtered()
            await self._publish(event_filtered)
        

    # ------------------------------------------------------------------
    # Publication EventBus
    # ------------------------------------------------------------------
    async def _publish(self, event: TradeSignalGenerated):
        self._logger.debug(f"event={event}")
        await self.event_bus.publish(event)
