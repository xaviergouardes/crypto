# trading_bot/main.py
#
# Test avec les bougies et historique sur 25 bougie d'une minutes
# Stratégie basée sur la pente de la SMA avec une période de 25 bougie de 1 minutes
#

import asyncio
from datetime import datetime, timedelta

from trading_bot.core.event_bus import EventBus

from trading_bot.backtests.candle_snapshot_history_from_csv import CandleSnapShotHistoryFromCsv
from trading_bot.backtests.candle_stream_from_csv import CandleStreamFromCSV

from trading_bot.indicator_engine.indicator_moving_average import IndicatorMovingAverage
from trading_bot.indicator_engine.indicator_atr import IndicatorATR
from trading_bot.indicator_engine.indicator_avg_volume import IndicatorAvgVolume
from trading_bot.indicator_engine.indicator_swing_detector import IndicatorSwingDetector
from trading_bot.strategy.strategy_breakout_ema200 import StrategyBreakoutEMA200 

from trading_bot.risk_manager.risk_manager import RiskManager 

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition

from trading_bot.trade_journal.trade_journal import TradeJournal

async def main():
    event_bus = EventBus()
    
    candel_snapshot_history =  CandleSnapShotHistoryFromCsv(
        event_bus=event_bus,
        # csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHBTC_historique_court.csv",
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHUSDC_5m_historique_20250901_20251017.csv",
        symbol="ETHBTC",
        period=timedelta(minutes=5),
        history_limit=200
    )
    candel_stream = CandleStreamFromCSV(
        event_bus=event_bus,
        # csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHBTC_historique_court.csv",
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHUSDC_5m_historique_20250901_20251017.csv",        
        period=timedelta(minutes=5),
        symbol="ETHBTC",
        history_limit=200
    )

    indicator_ema_200_candle = IndicatorMovingAverage(event_bus, period=200, mode="EMA")  # SMA
    indicator_atr = IndicatorATR(event_bus, period=14)
    indicator_avg_volume = IndicatorAvgVolume(event_bus, period=14)
    indicator_swing_detector = IndicatorSwingDetector(event_bus, lookback=3, min_distance=10, min_strength=2)
    strategy_engine = StrategyBreakoutEMA200(event_bus, atr_multiple=10)      
    
    risk_manager = RiskManager(event_bus, tp_percent=0.4, sl_percent=0.2) 
 

    trader = TraderOnlyOnePosition(event_bus)
    
    trader_journal = TradeJournal(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        candel_snapshot_history.run(),
        candel_stream.run(),
        indicator_ema_200_candle.run(),
        indicator_atr.run(),
        indicator_avg_volume.run(),
        indicator_swing_detector.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run()
    )


if __name__ == "__main__":
    asyncio.run(main())
