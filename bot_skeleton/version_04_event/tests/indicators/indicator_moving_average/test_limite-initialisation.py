from datetime import datetime, timedelta
import pytest

from trading_bot.core.events import CandleHistoryReady, IndicatorUpdated
from trading_bot.indicators.moving_average.moving_average import MovingAverage
from trading_bot.core.event_bus import EventBus

# Mock pour une bougie
class MockCandle:
    def __init__(self, close, start_time=None, end_time=None):
        self.close = close
        self.start_time = start_time or datetime.now()
        self.end_time = end_time or (self.start_time + timedelta(minutes=1))
        
    def __repr__(self):
        return f"MockCandle(close={self.close})"
    
def test_invalid_mode():
    bus = EventBus()
    with pytest.raises(ValueError):
        MovingAverage(bus, period=20, mode="INVALID")


@pytest.mark.asyncio
async def test_period_1_initialization():
    event_bus = EventBus()
    indicator = MovingAverage(event_bus, period=1, mode="SMA")

    # Stocker les événements publiés pour vérification
    published = []
    async def capture(event):
        print(f"==> Capture !!! {event}")
        published.append(event)
    event_bus.subscribe(IndicatorUpdated, capture)

    # Envoi d'un historique
    history = [MockCandle(10)]
    event = CandleHistoryReady(
                symbol="ethusdc",
                timestamp=datetime.now(),
                period="5m",
                candles=history
            )
    await indicator.on_history_ready(event)

    # Historique pas assez grand pour calculer 1 bougie et période = 3
    assert indicator._initialized is True

    # Vérifier qu'il n'y a 1 event de publié
    assert len(published) == 1 
    assert published[-1].values["sma_value"] == 10