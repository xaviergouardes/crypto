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
from trading_bot.strategy.strategy_ema_cross_fast_slow import StrategyEmaCrossFastSlowEngine 

from trading_bot.risk_manager.risk_manager import RiskManager 
from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition
from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.keyboard_event import KeyboardEvent

async def main():
    event_bus = EventBus()
    
    candel_snapshot_history =  CandleSnapShotHistoryFromCsv(
        event_bus=event_bus,
        # csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHBTC_historique_court.csv",
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHUSDC_3m_historique_20250901_20251017.csv",
        symbol="ETHBTC",
        period=timedelta(minutes=3),
        history_limit=200
    )
    candel_stream = CandleStreamFromCSV(
        event_bus=event_bus,
        # csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHBTC_historique_court.csv",
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHUSDC_3m_historique_20250901_20251017.csv",        period=timedelta(minutes=3),
        symbol="ETHBTC",
        history_limit=200
    )

    indicator_ema_slow_candle = IndicatorMovingAverage(event_bus, period=200, mode="EMA")  # SMA
    indicator_ema_fast_candle = IndicatorMovingAverage(event_bus, period=18, mode="EMA")  # SMA
    
    strategy_engine = StrategyEmaCrossFastSlowEngine(event_bus, periode_slow_ema=200, periode_fast_ema=18, slope_threshold=1)         # génère les signaux
    
    risk_manager = RiskManager(event_bus, tp_percent=0.5, sl_percent=0.25) # cible environ 6 usd pour 4000 

    trader = TraderOnlyOnePosition(event_bus)
    
    trader_journal = TradeJournal(event_bus)
    keyboard_event = KeyboardEvent(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        candel_snapshot_history.run(),
        candel_stream.run(),
        indicator_ema_slow_candle.run(),
        indicator_ema_fast_candle.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run(),
        keyboard_event.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
