from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import IndicatorUpdated


class SignalEmitter:
    """Émet des signaux via EventBus."""
    _logger = Logger.get("IndicatorEmaCrossDetector")

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def emit(self, symbol: str, timestamp, signal: str, fast_period: int, slow_period: int):
        event = IndicatorUpdated(
                    symbol=symbol,
                    timestamp=timestamp,
                    values={
                        "type": "IndicatorEmaCrossDetector",
                        "signal": signal,
                        "fast_period": fast_period,
                        "slow_period": slow_period,
                    },
                )
        await self.event_bus.publish(event)
        # self._logger.debug(f"Event émis : {event}")
       