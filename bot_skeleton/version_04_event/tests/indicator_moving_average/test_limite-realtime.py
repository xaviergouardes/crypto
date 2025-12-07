from datetime import datetime, timedelta
import pytest

from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated
from trading_bot.indicators.indicator_moving_average import IndicatorMovingAverage
from trading_bot.core.event_bus import Event, EventBus

# Mock pour une bougie
class MockCandle:
    def __init__(self, close, start_time=None, end_time=None):
        self.close = close
        self.start_time = start_time or datetime.now()
        self.end_time = end_time or (self.start_time + timedelta(minutes=1))
        
    def __repr__(self):
        return f"MockCandle(close={self.close})"
    
@pytest.mark.asyncio
async def test_on_close_wrong_symbol():
    event_bus = EventBus()
    indicator = IndicatorMovingAverage(event_bus, period=13, mode="SMA")
    indicator._initialized = True # on se demande si c'est vraiment bien d'utiliser directement une varibale privée
    indicator.symbol = "ETH"

    # Stocker les événements publiés pour vérification
    published = []
    async def capture(event):
        published.append(event)
    event_bus.subscribe(IndicatorUpdated, capture)

    class MockEvent:
        symbol = "BTC"
        class candle:
            close = 123
            end_time = datetime.now()

    await indicator.on_candle_close(MockEvent())

    # Historique pas assez grand pour calculer 1 bougie et période = 3
    assert indicator.current_value is None

    # Vérifier qu'il n'y a pas d'elements pubié
    assert len(published) == 0 


@pytest.mark.asyncio
async def test_on_close_first_update():
    event_bus = EventBus()
    indicator = IndicatorMovingAverage(event_bus, period=3, mode="EMA")
    indicator.symbol = "ethusdc"

    # Stocker les événements publiés pour vérification
    published = []
    async def capture(event):
        published.append(event)
    event_bus.subscribe(IndicatorUpdated, capture)

    # Envoi d'un historique 
    history = [MockCandle(10), MockCandle(10), MockCandle(10)] 
    event = CandleHistoryReady(
                symbol="ethusdc",
                timestamp=datetime.now(),
                period="5m",
                candles=history
            )
    await indicator.on_history_ready(event)

    # calcul de la prochaine valeur => 
    # La formule EMA standard :
    #     EMAnew​=(Pricenew​−EMAold​)×multiplier+EMAold​ 
    #         • multiplier = 2 / (period + 1) → ici 2 / (3 + 1) = 0.5
    #         • Valeur précédente (EMA_old) = 10
    #         • Nouvelle valeur (Price_new) = 13
    #     Donc :
    #     EMAnew​=(13−10)×0.5+10=3×0.5+10=1.5+10=11.5
    event = CandleClose(symbol="ethusdc", candle=MockCandle(13))
    await indicator.on_candle_close(event)

    assert indicator.current_value == pytest.approx(11.5)

    assert len(published) == 2, "Un seul event doit etre publié"
    last_event = published[-1]
    assert last_event.values["ema_candle"] is not None, "'ema_candle' est None"
    assert last_event.values["ema_candle"] == pytest.approx(11.5), "'ema_candle' n'a pas la valeur attendu"
    assert last_event.values["ema_candle_period"] == 3, "'ema_candle_period' est None"


@pytest.mark.asyncio
async def test_sma_sliding_window():
    event_bus = EventBus()
    indicator = IndicatorMovingAverage(event_bus, period=3, mode="SMA")
    indicator.symbol = "ethusdc"

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

    # calcul de la prochaine valeur => 
    # nouveau SMA = (20 + 30 + 40) / 3 = 30
    event = CandleClose(symbol="ethusdc", candle=MockCandle(40))
    await indicator.on_candle_close(event)

    assert indicator.current_value == 30

    assert len(published) == 2, "Un seul event doit etre publié"
    last_event = published[-1]
    assert last_event.values["sma_candle"] is not None, "'sma_candle' est None"
    assert last_event.values["sma_candle"] == 30, "'sma_candle' n'a pas la valeur attendu"
    assert last_event.values["sma_candle_period"] == 3, "'sma_candle_period' est None"