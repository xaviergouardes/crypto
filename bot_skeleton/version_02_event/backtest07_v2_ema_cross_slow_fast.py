# trading_bot/main.py
#
# Test avec les bougies et historique sur 25 bougie d'une minutes
# Stratégie basée sur la pente de la SMA avec une période de 25 bougie de 1 minutes
#

import asyncio
from datetime import timedelta

from trading_bot.core.event_bus import EventBus

from trading_bot.backtests.candle_snapshot_history_from_csv import CandleSnapShotHistoryFromCsv
from trading_bot.backtests.candle_stream_from_csv import CandleStreamFromCSV

from trading_bot.indicator_engine.indicator_moving_average import IndicatorMovingAverage
from trading_bot.indicator_engine.indicator_ema_cross_detector import IndicatorEmaCrossDetector
from trading_bot.indicator_engine.indicator_atr import IndicatorATR

from trading_bot.strategy.strategy_ema_cross_fast_slow_v2 import StrategyEmaCrossFastSlowEngineV2 

from trading_bot.risk_manager.risk_manager import RiskManager 
from trading_bot.risk_manager.risk_manager_by_atr import RiskManagerByAtr

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition
from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.keyboard_event import KeyboardEvent

async def main():
    event_bus = EventBus()
    
    fast_period = 21
    slow_period = 200

    candel_snapshot_history =  CandleSnapShotHistoryFromCsv(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250701_20251023.csv",
        symbol="ETHBTC",
        period=timedelta(minutes=5),
        history_limit=slow_period
    )
    candel_stream = CandleStreamFromCSV(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250701_20251023.csv",        
        period=timedelta(minutes=5),
        symbol="ETHBTC",
        history_limit=slow_period
    )


    indicator_ema_fast_candle = IndicatorMovingAverage(event_bus, period=fast_period, mode="EMA")  # SMA
    indicator_ema_slow_candle = IndicatorMovingAverage(event_bus, period=slow_period, mode="EMA")  # SMA
    indicator_cross_detector = IndicatorEmaCrossDetector(event_bus, fast_period=fast_period, slow_period=slow_period, buffer_size=2, slope_threshold=2.2)
     
    indicator_atr = IndicatorATR(event_bus, period=14)

    strategy_engine = StrategyEmaCrossFastSlowEngineV2(event_bus, periode_slow_ema=slow_period, periode_fast_ema=fast_period)         # génère les signaux
    
    risk_manager = RiskManagerByAtr(event_bus, atr_tp_mult=2, atr_sl_mult=1.25)

    trader = TraderOnlyOnePosition(event_bus)
    
    trader_journal = TradeJournal(event_bus)
    keyboard_event = KeyboardEvent(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        candel_snapshot_history.run(),
        candel_stream.run(),
        indicator_ema_slow_candle.run(),
        indicator_ema_fast_candle.run(),
        indicator_cross_detector.run(),
        indicator_atr.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run(),
        keyboard_event.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
