from datetime import datetime, timedelta
import pytest

from trading_bot.core.events import CandleHistoryReady, IndicatorUpdated
from trading_bot.indicators.moving_average.moving_average import IndicatorMovingAverage
from trading_bot.core.event_bus import EventBus

# Mock pour une bougie
class MockCandle:
    def __init__(self, close, start_time=None, end_time=None):
        self.close = close
        self.start_time = start_time or datetime.now()
        self.end_time = end_time or (self.start_time + timedelta(minutes=1))
        
    def __repr__(self):
        return f"MockCandle(close={self.close})"
    
class MockHistory:
    symbol = "BTC"
    candles = []


@pytest.mark.asyncio
async def test_history_empty():
    event_bus = EventBus()
    indicator = IndicatorMovingAverage(event_bus, period=13, mode="SMA")

    # Stocker les événements publiés pour vérification
    published = []
    async def capture(event):
        published.append(event)
    event_bus.subscribe(IndicatorUpdated, capture)

    # Envoi d'un historique VIDE
    history = []
    event = CandleHistoryReady(
                symbol="ethusdc",
                timestamp=datetime.now(),
                period="5m",
                candles=history
            )
    await indicator.on_history_ready(event)

    # Historique pas assez grand pour calculer 1 bougie et période = 3
    assert indicator._initialized is False

    # Vérifier qu'il n'y a pas d'elements pubié
    assert len(published) == 0 


@pytest.mark.asyncio
async def test_history_not_enough_candles():
    event_bus = EventBus()
    indicator = IndicatorMovingAverage(event_bus, period=20, mode="EMA")

    # Stocker les événements publiés pour vérification
    published = []
    async def capture(event):
        published.append(event)
    event_bus.subscribe(IndicatorUpdated, capture)

    # Envoi d'un historique 
    history = [MockCandle(i) for i in range(10)] 
    event = CandleHistoryReady(
                symbol="ethusdc",
                timestamp=datetime.now(),
                period="5m",
                candles=history
            )
    await indicator.on_history_ready(event)

    # Historique pas assez grand pour calculer 1 bougie et période = 3
    assert not indicator._initialized

    # Vérifier qu'il n'y a pas d'elements pubié
    assert len(published) == 0 