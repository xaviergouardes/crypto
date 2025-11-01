# trading_bot/main.py
#
#

import asyncio
from datetime import datetime, timedelta

from trading_bot.core.event_bus import EventBus

from trading_bot.backtests.candle_snapshot_history_from_csv import CandleSnapShotHistoryFromCsv
from trading_bot.backtests.candle_stream_from_csv import CandleStreamFromCSV

from trading_bot.indicator_engine.indicator_atr import IndicatorATR
from trading_bot.indicator_engine.indicator_simple_swing_detector import IndicatorSimpleSwingDetector
from trading_bot.strategy.strategy_simple_sweep_swing import  StrategySimpleSweepSwingEngine

from trading_bot.risk_manager.risk_manager_portefolio import RiskManagerPortefolio 
from trading_bot.risk_manager.risk_manager import RiskManager 

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition

from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.portefolio_manager import PortefolioManager
from trading_bot.trade_journal.keyboard_event import KeyboardEvent

async def main():
    event_bus = EventBus()
    
    candel_snapshot_history =  CandleSnapShotHistoryFromCsv(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250901_20251031.csv",
        symbol="ETHBTC",
        period=timedelta(minutes=5),
        history_limit=200
    )
    candel_stream = CandleStreamFromCSV(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250901_20251031.csv",        
        period=timedelta(minutes=5),
        symbol="ETHBTC",
        history_limit=200
    )

    indicator_atr = IndicatorATR(event_bus, period=14)
    indicator_swing_detector = IndicatorSimpleSwingDetector(event_bus, lookback=5, history_window=150)

    strategy_engine = StrategySimpleSweepSwingEngine(event_bus)      
    
    # risk_manager = RiskManagerPortefolio(event_bus, tp_percent=1, sl_percent=0.6, solde_inital_disponible=None) 
    risk_manager = RiskManager(event_bus, tp_percent=1, sl_percent=0.6, solde_disponible=1000) 
 
    trader = TraderOnlyOnePosition(event_bus)
    
    trader_journal = TradeJournal(event_bus)
    portefolio_manager = PortefolioManager(event_bus, starting_usdc=1000)
    keyboard_event = KeyboardEvent(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        candel_snapshot_history.run(),
        candel_stream.run(),
        indicator_atr.run(),
        indicator_swing_detector.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run(),
        # portefolio_manager.run(),
        keyboard_event.run()
    )


if __name__ == "__main__":
    asyncio.run(main())
