import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import IndicatorUpdated
from trading_bot.indicators.ema_cross_detector.ema_cross_detector import IndicatorEmaCrossDetector


# -----------------------------
# Dummy candle for tests
# -----------------------------
@dataclass
class DummyCandle:
    close: float = 0.0
    end_time: datetime = datetime.now(timezone.utc)


# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def event_bus():
    return EventBus()

@pytest.fixture
def detector(event_bus):
    return IndicatorEmaCrossDetector(
        event_bus,
        fast_period=3,
        slow_period=5,
        buffer_size=2,
        slope_threshold=0
    )


# -----------------------------
# 1️⃣ Test buffer update
# -----------------------------
@pytest.mark.asyncio
async def test_update_buffers(detector):
    ts = datetime.now(timezone.utc)

    # Fast EMA
    updated_fast, updated_slow = detector._update_buffers(3, 10, ts)
    assert updated_fast is True
    assert updated_slow is False
    assert detector.fast_buffer.last_values() == [10]

    # Slow EMA
    updated_fast, updated_slow = detector._update_buffers(5, 20, ts)
    assert updated_fast is False
    assert updated_slow is True
    assert detector.slow_buffer.last_values() == [20]


# -----------------------------
# 2️⃣ Both updated
# -----------------------------
def test_both_ema_updated(detector):
    assert detector._both_ema_updated() is False
    now = datetime.now(timezone.utc)
    detector.last_fast_update = now
    detector.last_slow_update = now
    assert detector._both_ema_updated() is True


# -----------------------------
# 3️⃣ Sync check
# -----------------------------
def test_ema_updates_synchronized(detector):
    now = datetime.now(timezone.utc)
    detector.last_fast_update = now
    detector.last_slow_update = now + timedelta(seconds=0.5)
    assert detector._ema_updates_synchronized() is True

    detector.last_slow_update = now + timedelta(seconds=2)
    assert detector._ema_updates_synchronized() is False


# -----------------------------
# 4️⃣ Crossing detection (bullish)
# -----------------------------
@pytest.mark.asyncio
async def test_handle_event_bullish(detector):
    ts = datetime.now(timezone.utc)
    symbol = "EURUSD"

    published = []

    async def capture(event):
        published.append(event)

    detector.event_bus.subscribe(IndicatorUpdated, capture)

    dummy = DummyCandle(close=0.0, end_time=ts)

    slow_events = [20, 21]
    fast_events = [19, 22]

    # Slow EMA d’abord
    for v in slow_events:
        await detector.handle_indicator_updated(IndicatorUpdated(
            symbol=symbol,
            candle=dummy,
            values={"ema_period": detector.slow_period, "ema_value": v}
        ))

    # Fast EMA ensuite → croisement bullish
    for v in fast_events:
        await detector.handle_indicator_updated(IndicatorUpdated(
            symbol=symbol,
            candle=dummy,
            values={"ema_period": detector.fast_period, "ema_value": v}
        ))

    # Encore une fast EMA pour déclencher
    await detector.handle_indicator_updated(IndicatorUpdated(
        symbol=symbol,
        candle=dummy,
        values={"ema_period": detector.fast_period, "ema_value": 23}
    ))

    await asyncio.sleep(0.05)

    assert any(
        e.values.get("signal") == "bullish"
        for e in published
    ), f"Aucun signal bullish détecté. Events = {published}"


# -----------------------------
# 5️⃣ Invalid event
# -----------------------------
@pytest.mark.asyncio
async def test_handle_event_invalid(detector):
    ts = datetime.now(timezone.utc)
    dummy = DummyCandle(close=0.0, end_time=ts)

    await detector.handle_indicator_updated(IndicatorUpdated(
        symbol="EURUSD",
        candle=dummy,
        values={}
    ))

    assert True
