import pytest
import asyncio
from datetime import datetime, timedelta
from collections import deque

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated
from trading_bot.indicators.moving_average.moving_average import IndicatorMovingAverage

# Mock pour une bougie
class MockCandle:
    def __init__(self, close, start_time=None, end_time=None):
        self.close = close
        self.start_time = start_time or datetime.now()
        self.end_time = end_time or (self.start_time + timedelta(minutes=1))
        
    def __repr__(self):
        return f"MockCandle(close={self.close})"

@pytest.mark.asyncio
async def test_sma_calculation():
    event_bus = EventBus()
    indicator = IndicatorMovingAverage(event_bus, period=3, mode="SMA")

    # Stocker les événements publiés pour vérification
    published = []
    async def capture(event):
        published.append(event)
    event_bus.subscribe(IndicatorUpdated, capture)

    # Envoi d'un historique
    history = [MockCandle(10), MockCandle(20), MockCandle(30)]
    event = CandleHistoryReady(
                symbol="ethusdc",
                timestamp=datetime.now(),
                period="5m",
                candles=history
            )
    await indicator.on_history_ready(event)

    # SMA = (10+20+30)/3 = 20
    assert indicator._initialized

    # Ajouter une nouvelle bougie et vérifier mise à jour SMA
    await indicator.on_candle_close(CandleClose(symbol="ethusdc", candle=MockCandle(40)))
    # Nouvelle SMA = (20+30+40)/3 = 30

    # Vérifier qu'un événement a été publié
    assert len(published) == 2  # initial + update

    # Le dernier evetn publié doit avec une valeur EMA
    last_event = published[-1]
    assert last_event.values["sma_value"] is not None, "'sma_candle' est None"
    assert last_event.values["sma_value"] == 30.0, "'sma_candle' n'a pas la valeur attendu"
    assert last_event.values["sma_period"] == 3, "'sma_period' est None"

@pytest.mark.asyncio
async def test_ema_calculation():
    event_bus = EventBus()
    indicator = IndicatorMovingAverage(event_bus, period=3, mode="EMA")

    published = []
    async def capture(event):
        published.append(event)
    event_bus.subscribe(IndicatorUpdated, capture)

    # Envoi d'un historique
    history = [MockCandle(10), MockCandle(20), MockCandle(30)]
    event = CandleHistoryReady(
                symbol="ethusdc",
                timestamp=datetime.now(),
                period="5m",
                candles=history
            )
    await indicator.on_history_ready(event)

    # EMA initial approximatif (poids calculés automatiquement)
    assert indicator._initialized


    # Ajouter une nouvelle bougie
    await indicator.on_candle_close(CandleClose(symbol="ethusdc", candle=MockCandle(40)))
    # EMA doit avoir changé

    # Vérifier publication
    assert len(published) >= 2

    # Le dernier evetn publié doit avec une valeur EMA
    assert "ema_value" in published[-1].values, "La clé 'ema_value' n'existe pas"
    assert "ema_period" in published[-1].values, "La clé 'ema_period' n'existe pas"

    last_event = published[-1]
    assert last_event.values["ema_value"] is not None, "'ema_value' est None"
    assert last_event.values["ema_period"] == 3, "'ema_period' est None"