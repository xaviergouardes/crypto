# trading_bot/trader/keyboard_event.py
import asyncio
import signal
import time
from typing import Optional
from datetime import datetime

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import StopBot


class KeyboardEvent:
    """
    Intercepte Ctrl+C (SIGINT), publie un événement StopBot sur le bus,
    attend le traitement du journal, puis arrête proprement toutes les tâches asyncio.
    """

    def __init__(self, event_bus: EventBus, shutdown_timeout: float = 5.0):
        self.event_bus = event_bus
        self.shutdown_timeout = shutdown_timeout
        self._stop_event = asyncio.Event()
        self._shutdown_task: Optional[asyncio.Task] = None
        self._stopped = False

    async def _publish_stop(self):
        """Publie l'événement StopBot et attend sa propagation."""
        try:
            result = self.event_bus.publish(StopBot(timestamp=time.time()))
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] ⚠️ Erreur lors du publish StopBot : {e!r}")

    async def _shutdown(self):
        """Publie StopBot puis annule proprement toutes les autres tâches."""
        if self._stopped:
            return
        self._stopped = True

        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] 🛑 Arrêt propre demandé...")
        try:
            await self._publish_stop()
        except Exception as e:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] Erreur publish StopBot: {e!r}")

        # Récupère toutes les tâches sauf la tâche actuelle
        current = asyncio.current_task()
        tasks = [t for t in asyncio.all_tasks() if t is not current and not t.done()]

        if tasks:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] ⏳ Annulation de {len(tasks)} tâches actives...")
            for t in tasks:
                t.cancel()
            try:
                await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True),
                                       timeout=self.shutdown_timeout)
            except asyncio.TimeoutError:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] ⌛ Timeout — certaines tâches n'ont pas répondu.")
            except Exception as e:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] Erreur lors de l'annulation : {e!r}")

        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] ✅ Arrêt propre terminé.")
        self._stop_event.set()

    def _on_signal(self):
        """Handler appelé quand Ctrl+C est détecté."""
        if self._shutdown_task is None or self._shutdown_task.done():
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] Ctrl+C détecté — arrêt propre en cours...")
            loop = asyncio.get_running_loop()
            self._shutdown_task = loop.create_task(self._shutdown())

    async def stop(self):
        """Arrêt manuel (utile quand toutes les tâches se terminent naturellement)."""
        await self._shutdown()

    async def run(self, monitored_tasks: Optional[list[asyncio.Task]] = None):
        """
        Démarre la surveillance du clavier et attend l'arrêt complet.
        Si `monitored_tasks` est fourni, le KeyboardEvent s'arrête automatiquement
        lorsque toutes ces tâches sont terminées.
        """
        loop = asyncio.get_running_loop()

        try:
            loop.add_signal_handler(signal.SIGINT, self._on_signal)
            try:
                loop.add_signal_handler(signal.SIGTERM, self._on_signal)
            except Exception:
                pass
        except NotImplementedError:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] add_signal_handler non supporté sur cette plateforme (fallback activé)")

        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [KeyboardEvent] En écoute (Ctrl+C pour arrêter)...")

        # Si des tâches sont surveillées, on attend leur complétion ou Ctrl+C
        if monitored_tasks:
            done, _ = await asyncio.wait(
                [*monitored_tasks, self._stop_event.wait()],
                return_when=asyncio.FIRST_COMPLETED
            )
            # si ce n’est pas Ctrl+C, on déclenche un arrêt propre
            if not self._stop_event.is_set():
                await self.stop()
        else:
            await self._stop_event.wait()

        # Nettoyage des handlers
        try:
            loop.remove_signal_handler(signal.SIGINT)
            loop.remove_signal_handler(signal.SIGTERM)
        except Exception:
            pass
