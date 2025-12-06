from datetime import datetime
import pytest

from bot_skeleton.version_04_event.trading_bot.core.events import IndicatorUpdated
from trading_bot.indicators.indicator_moving_average import IndicatorMovingAverage
from trading_bot.core.event_bus import EventBus

def test_invalid_mode():
    bus = EventBus()
    with pytest.raises(ValueError):
        IndicatorMovingAverage(bus, period=20, mode="INVALID")


