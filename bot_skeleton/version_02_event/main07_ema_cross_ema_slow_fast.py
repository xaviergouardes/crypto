# trading_bot/main.py
#
# Test avec les bougies et historique sur 25 bougie d'une minutes
# Stratégie basée sur la pente de la SMA avec une période de 25 bougie de 1 minutes
#

import asyncio
from datetime import datetime, timedelta

from trading_bot.core.event_bus import EventBus


from trading_bot.market_data.price_stream import PriceStream
from trading_bot.market_data.candle_snapshot_history import CandleSnapShotHistory
from trading_bot.market_data.candle_stream import CandleStream

from trading_bot.indicator_engine.indicator_moving_average import IndicatorMovingAverage
from trading_bot.strategy.strategy_ema_cross_fast_slow import StrategyEmaCrossFastSlowEngine 

from trading_bot.risk_manager.risk_manager import RiskManager 
from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition
from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.keyboard_event import KeyboardEvent


async def main():
    event_bus = EventBus()

    # Initialisation des modules
    price_stream = PriceStream(event_bus)               # récupère les prix 
    
    candel_snapshot_history = CandleSnapShotHistory(event_bus, period=timedelta(minutes=1), history_limit=25)
    candel_stream = CandleStream(event_bus)

    indicator_ema_25_candle = IndicatorMovingAverage(event_bus, period=25, mode="EMA")  # SMA
    indicator_ema_9_candle = IndicatorMovingAverage(event_bus, period=9, mode="EMA")  # SMA
    
    strategy_engine = StrategyEmaCrossFastSlowEngine(event_bus, periode_slow_ema=25, periode_fast_ema=9, slope_threshold=0.05)         # génère les signaux
    
    #risk_manager = RiskManager(event_bus, tp_percent=0.02, sl_percent=0.02)
    risk_manager = RiskManager(event_bus, tp_percent=0.1, sl_percent=0.1) 
    
    trader = TraderOnlyOnePosition(event_bus)
    
    trader_journal = TradeJournal(event_bus)
    keyboard_event = KeyboardEvent(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        price_stream.run(),
        candel_snapshot_history.run(),
        candel_stream.run(),
        indicator_ema_25_candle.run(),
        indicator_ema_9_candle.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run(),
        keyboard_event.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
