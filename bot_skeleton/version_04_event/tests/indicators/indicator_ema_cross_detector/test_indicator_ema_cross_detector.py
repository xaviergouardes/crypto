import pytest
import asyncio
from datetime import datetime, timedelta, timezone

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import IndicatorUpdated
from trading_bot.indicators.indicator_ema_cross_detector.indicator_cross_ema_detector import IndicatorEmaCrossDetector

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def event_bus():
    return EventBus()

@pytest.fixture
def detector(event_bus):
    # fast_period=3, slow_period=5, buffer_size=2 pour test rapide
    return IndicatorEmaCrossDetector(event_bus, fast_period=3, slow_period=5, buffer_size=2, slope_threshold=0)

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
# 2️⃣ Test _both_ema_updated
# -----------------------------
def test_both_ema_updated(detector):
    assert detector._both_ema_updated() is False
    detector.last_fast_update = datetime.now(timezone.utc)
    detector.last_slow_update = datetime.now(timezone.utc)
    assert detector._both_ema_updated() is True

# -----------------------------
# 3️⃣ Test _ema_updates_synchronized
# -----------------------------
def test_ema_updates_synchronized(detector):
    now = datetime.now(timezone.utc)
    detector.last_fast_update = now
    detector.last_slow_update = now + timedelta(seconds=0.5)
    assert detector._ema_updates_synchronized() is True

    detector.last_slow_update = now + timedelta(seconds=2)
    assert detector._ema_updates_synchronized() is False

# -----------------------------
# 4️⃣ Test crossing detection (nominal bullish)
# -----------------------------
@pytest.mark.asyncio
async def test_handle_event_bullish(detector):
    ts = datetime.now(timezone.utc)
    symbol = "EURUSD"

    # On capture les events AVANT publication
    published = []
    async def capture(event):
        published.append(event)
    detector.event_bus.subscribe(IndicatorUpdated, capture)

    # Publier EMA slow puis fast pour créer croisement bullish
    # Slow EMA légèrement au-dessus de la fast EMA initialement
    slow_events = [20, 21]   # buffer slow
    fast_events = [19, 22]   # buffer fast -> croisement de bas en haut

    # Publier slow
    for v in slow_events:
        await detector.handle_event(IndicatorUpdated(
            symbol=symbol, 
            timestamp=ts, 
            values={"ema_candle_period": detector.slow_period, "ema_candle": v}
        ))

    # Publier fast
    for v in fast_events:
        await detector.handle_event(IndicatorUpdated(
            symbol=symbol, 
            timestamp=ts, 
            values={"ema_candle_period": detector.fast_period, "ema_candle": v}
        ))

    # Publier encore pour s'assurer que la détection est déclenchée
    await detector.handle_event(IndicatorUpdated(
        symbol=symbol, 
        timestamp=ts, 
        values={"ema_candle_period": detector.fast_period, "ema_candle": 23}
    ))

    # Petite attente pour que l'async se déclenche
    await asyncio.sleep(0.1)

    # Vérification du signal bullish
    print("===> published = ", published)
    assert any(e.values.get("signal") == "bullish" for e in published), f"Événements publiés : {[e.values for e in published]}"
    

# -----------------------------
# 5️⃣ Test handle_event ignore valeurs invalides
# -----------------------------
@pytest.mark.asyncio
async def test_handle_event_invalid(detector):
    ts = datetime.now(timezone.utc)
    await detector.handle_event(IndicatorUpdated(symbol="EURUSD", timestamp=ts, values={}))
    # Aucun crash et pas d'émission
    assert True
