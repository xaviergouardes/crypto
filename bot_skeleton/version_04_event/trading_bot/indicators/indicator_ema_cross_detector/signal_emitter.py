from bot_skeleton.version_04_event.trading_bot.core.event_bus import EventBus
from bot_skeleton.version_04_event.trading_bot.core.events import IndicatorUpdated


class SignalEmitter:
    """Émet des signaux via EventBus."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def emit(self, symbol: str, timestamp, signal: str, fast_period: int, slow_period: int):
        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=symbol,
                timestamp=timestamp,
                values={
                    "type": "IndicatorEmaCrossDetector",
                    "signal": signal,
                    "fast_period": fast_period,
                    "slow_period": slow_period,
                },
            )
        )