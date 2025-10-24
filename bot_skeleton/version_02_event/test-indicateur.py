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

from trading_bot.indicator_engine.indicator_simple_swing_detector import IndicatorSimpleSwingDetector
from trading_bot.indicator_engine.indicator_premium_discount import IndicatorPremiumDiscount

async def main():
    event_bus = EventBus()
    
    candel_snapshot_history =  CandleSnapShotHistoryFromCsv(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20251024_20251025.csv",
       symbol="ETHBTC",
        period=timedelta(minutes=5),
        history_limit=100
    )
    candel_stream = CandleStreamFromCSV(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20251024_20251025.csv",
       period=timedelta(minutes=5),
        symbol="ETHBTC",
        history_limit=100
    )

    indicator_swing_detector = IndicatorSimpleSwingDetector(event_bus, lookback= 5, history_window=100) 
    indicator_premium_discount = IndicatorPremiumDiscount(event_bus) 

    # Lancer tous les modules
    await asyncio.gather(
        candel_snapshot_history.run(),
        candel_stream.run(),
        indicator_swing_detector.run(),
        indicator_premium_discount.run(),
    )

if __name__ == "__main__":
    asyncio.run(main())
