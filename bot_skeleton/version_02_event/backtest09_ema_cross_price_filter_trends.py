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

from trading_bot.indicator_engine.indicator_atr import IndicatorATR
from trading_bot.indicator_engine.indicator_moving_average import IndicatorMovingAverage

from trading_bot.strategy.strategy_ema_cross_price_filter_trend import StrategyEmaCrossPriceFilterTrendsEngine

from trading_bot.risk_manager.risk_manager import RiskManager 
from trading_bot.risk_manager.risk_manager_by_atr import RiskManagerByAtr

from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition
from trading_bot.trade_journal.trade_journal import TradeJournal

async def main():
    event_bus = EventBus()
    
    candel_snapshot_history_csv =  CandleSnapShotHistoryFromCsv(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHUSDC_5m_historique_20250701_20251019.csv",
        symbol="ETHBTC",
        period=timedelta(minutes=5),
        history_limit=300
    )
    candel_stream_csv = CandleStreamFromCSV(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHUSDC_5m_historique_20250701_20251019.csv",        
        period=timedelta(minutes=5),
        symbol="ETHBTC",
        history_limit=300
    )

    indicator_ema_trend = IndicatorMovingAverage(event_bus, period=300, mode="EMA")  
    indicator_ema = IndicatorMovingAverage(event_bus, period=200, mode="EMA")  
    indicator_atr = IndicatorATR(event_bus, period=14)

    strategy_engine = StrategyEmaCrossPriceFilterTrendsEngine(event_bus, ema_trend_period=300, ema_band_with=0.001)         # génère les signaux

    #risk_manager = RiskManager(event_bus, tp_percent=0.5, sl_percent=0.25) # cible environ 6 usd pour 4000 
    risk_manager = RiskManagerByAtr(event_bus, atr_tp_mult=2, atr_sl_mult=1.25) # cible environ 6 usd pour 4000

    trader = TraderOnlyOnePosition(event_bus)
    
    trader_journal = TradeJournal(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        candel_snapshot_history_csv.run(),
        candel_stream_csv.run(),
        indicator_ema_trend.run(),
        indicator_ema.run(),
        indicator_atr.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run()
    )

if __name__ == "__main__":
    asyncio.run(main())



    # candel_stream_csv = CandleStreamFromCSV(
    #     event_bus=event_bus,
    #     csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHUSDC_5m_historique_20250701_20251019.csv",        
    #     period=timedelta(minutes=5),
    #     symbol="ETHBTC",
    #     history_limit=300
    # )

    # indicator_ema_trend = IndicatorMovingAverage(event_bus, period=300, mode="EMA")  
    # indicator_ema = IndicatorMovingAverage(event_bus, period=200, mode="EMA")  
    # indicator_atr = IndicatorATR(event_bus, period=14)

    # strategy_engine = StrategyEmaCrossPriceFilterTrendsEngine(event_bus, ema_trend_period=300, ema_band_with=0.001)         # génère les signaux

    # #risk_manager = RiskManager(event_bus, tp_percent=0.5, sl_percent=0.25) # cible environ 6 usd pour 4000 
    # risk_manager = RiskManagerByAtr(event_bus, atr_tp_mult=2, atr_sl_mult=1.25) # cible environ 6 usd pour 4000

    # trader = TraderOnlyOnePosition(event_bus)
    # trader_journal = TradeJournal(event_bus)

