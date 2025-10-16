# trading_bot/main.py
#
# Test avec les bougies et historique sur 25 bougie d'une minutes
# Stratégie basée sur la pente de la SMA avec une période de 25 bougie de 1 minutes
#

import asyncio
from datetime import datetime, timedelta

from trading_bot.core.event_bus import EventBus

from trading_bot.backtests.candle_snapshot_history_from_csv import CandleSnapShotHistoryFromCsv


async def main():
    event_bus = EventBus()
    
    candel_snapshot_history =  CandleSnapShotHistoryFromCsv(
        event_bus=event_bus,
        csv_path="/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_02_event/trading_bot/backtests/ETHBTC_historique.csv",
        symbol="ETHBTC",
        period=timedelta(minutes=3),
        history_limit=10
    )

    # Lancer tous les modules
    await asyncio.gather(
        candel_snapshot_history.run(),
    )

if __name__ == "__main__":
    asyncio.run(main())
