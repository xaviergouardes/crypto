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
from trading_bot.indicator_engine.indicator_atr import IndicatorATR

from trading_bot.strategy.strategy_ema_cross_fast_slow import StrategyEmaCrossFastSlowEngine 

from trading_bot.risk_manager.risk_manager_by_atr import RiskManagerByAtr

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition
from trading_bot.trade_journal.trade_journal import TradeJournal


async def main():
    event_bus = EventBus()

    # Initialisation des modules
    price_stream = PriceStream(event_bus)               # récupère les prix 
    
    candel_snapshot_history = CandleSnapShotHistory(event_bus, period=timedelta(minutes=5), history_limit=100)
    candel_stream = CandleStream(event_bus)

    indicator_ema_slow_candle = IndicatorMovingAverage(event_bus, period=100, mode="EMA")  # SMA
    indicator_ema_fast_candle = IndicatorMovingAverage(event_bus, period=21, mode="EMA")  # SMA
    indicator_atr = IndicatorATR(event_bus, period=14)

    strategy_engine = StrategyEmaCrossFastSlowEngine(event_bus, periode_slow_ema=100, periode_fast_ema=21, slope_threshold=3.5)         # génère les signaux
    
    risk_manager = RiskManagerByAtr(event_bus, atr_tp_mult=2, atr_sl_mult=1.25)
    
    trader = TraderOnlyOnePosition(event_bus)
    
    trader_journal = TradeJournal(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        price_stream.run(),
        candel_snapshot_history.run(),
        candel_stream.run(),
        indicator_ema_slow_candle.run(),
        indicator_ema_fast_candle.run(),
        indicator_atr.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
