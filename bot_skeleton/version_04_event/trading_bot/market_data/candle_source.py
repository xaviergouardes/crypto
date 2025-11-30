# trading_bot/data_market/candle_source.py

from abc import ABC, abstractmethod
import asyncio
from typing import override

from trading_bot.core.startable import Startable
from trading_bot.core.event_bus import EventBus


class CandleSource(Startable, ABC):

    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus

        # gestion du start/stop uniformisée
        self._stop_event = asyncio.Event()
        self._stream_task = None

    # ------------------- CYCLE DE VIE -------------------

    @override
    async def _on_start(self):
        """Démarre warmup puis le flux."""
        self._stop_event.clear()

        await self._warmup()
        self._stream_task = asyncio.create_task(self._stream_wrapper())

    @override
    def _on_stop(self):
        """Arrêt propre du flux."""
        self._stop_event.set()

        if self._stream_task:
            self._stream_task.cancel()


    # ------------------- LOGIQUE STANDARD -------------------

    async def _stream_wrapper(self):
        """Boucle gérée par CandleSource, implémentée par les enfants."""
        try:
            await self._stream()
        except asyncio.CancelledError:
            raise

    def should_stop(self):
        return self._stop_event.is_set()

    # ------------------- À IMPLÉMENTER -------------------

    @abstractmethod
    async def _warmup(self):
        """Récupère et publie les bougies de warmup."""
        pass

    @abstractmethod
    async def _stream(self):
        """Boucle du flux temps réel."""
        pass
