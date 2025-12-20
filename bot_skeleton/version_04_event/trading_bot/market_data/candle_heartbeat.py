import asyncio
from datetime import datetime, timezone
from trading_bot.core.logger import Logger
from trading_bot.core.events import CandleClose
from trading_bot.core.event_bus import EventBus
from trading_bot.core.startable import Startable


class CandleHeartbeatMonitor(Startable):
    """
    Heartbeat basé sur les événements CandleClose.
    Vérifie que le flux de candles reste actif en fonction
    de l'intervalle réel de la candle (en secondes).
    """

    logger = Logger.get("CandleHeartbeatMonitor")

    def __init__(
        self,
        event_bus: EventBus
    ):
        super().__init__()

        self.symbol = None
        self.tolerance_factor = 1.0

        self._last_candle_time: datetime | None = None
        self._interval_seconds: int | None = None

        self._task: asyncio.Task | None = None

        self.heartbeat = "alive"

        event_bus.subscribe(CandleClose, self._on_candle_close)

    # ------------------------------------------------------------------
    # Event handler
    # ------------------------------------------------------------------

    async def _on_candle_close(self, event: CandleClose):
        if not self.is_running():
            return

        self.symbol = event.symbol
        self._last_candle_time = datetime.now(timezone.utc)
        self._interval_seconds = event.candle.interval  # source de vérité

        # self.logger.debug(
        #     f"💓 CandleClose reçu ({self.symbol}) "
        #     f"[interval={self._interval_seconds}s]"
        # )

    # ------------------------------------------------------------------
    # Startable lifecycle
    # ------------------------------------------------------------------

    async def _on_start(self):
        self.logger.info("🫀 CandleHeartbeatMonitor démarré")
        self._task = asyncio.create_task(self._run())

    def _on_stop(self):
        if self._task:
            self._task.cancel()
            self._task = None

        self._last_candle_time = None
        self._interval_seconds = None

        self.logger.info("🛑 CandleHeartbeatMonitor arrêté")

    # ------------------------------------------------------------------
    # Heartbeat loop
    # ------------------------------------------------------------------

    async def _run(self):
        try:
            while True:
                if self._interval_seconds is None:
                    # self.logger.warning("⚠️ En attente du premier CandleClose...")
                    await asyncio.sleep(10)
                    continue

                max_delay = self._interval_seconds * self.tolerance_factor
                await asyncio.sleep(self._interval_seconds)

                if self._last_candle_time is None:
                    continue

                elapsed = (
                    datetime.now(timezone.utc) - self._last_candle_time
                ).total_seconds()

                if elapsed > max_delay:
                    self.heartbeat = "dead"
                    self.logger.error(
                        f"❌ Flux Candle mort ({self.symbol}) "
                        f"— dernier CandleClose il y a {int(elapsed)}s "
                        f"(max autorisé {int(max_delay)}s)"
                    )
                    # 👉 action possible ici (event, pause trading, restart feed)
                else:
                    self.heartbeat = "alive"
                    self.logger.debug(
                        f"✅ Flux Candle OK ({self.symbol}) "
                        f"— {int(elapsed)}s / {int(max_delay)}s"
                    )

        except asyncio.CancelledError:
            self.logger.debug("Heartbeat task annulée")
            raise
