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

from trading_bot.indicator_engine.indicator_swing_detector import IndicatorSwingDetector
from trading_bot.strategy.strategy_sweep_swing import StrategySweepSwingEngine 

from trading_bot.risk_manager.risk_manager import RiskManager 
from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition

from trading_bot.trade_journal.trade_journal import TradeJournal
from trading_bot.trade_journal.telegram_notifier import TelegramNotifier
from trading_bot.trade_journal.portfolio_manager import PortfolioManager

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

async def main():
    event_bus = EventBus()

    # Initialisation des modules
    price_stream = PriceStream(event_bus)               # récupère les prix 
    
    candel_snapshot_history = CandleSnapShotHistory(event_bus, period=timedelta(minutes=1), history_limit=25)
    candel_stream = CandleStream(event_bus)

    indicator_swing_detector = IndicatorSwingDetector(event_bus)  # SMA
    
    strategy_engine = StrategySweepSwingEngine(event_bus)         # génère les signaux
    
    #risk_manager = RiskManager(event_bus, tp_percent=0.02, sl_percent=0.02)
    risk_manager = RiskManager(event_bus, tp_percent=0.1, sl_percent=0.1) 
    
    trader = TraderOnlyOnePosition(event_bus)
    
    trader_journal = TradeJournal(event_bus)
    portefolio_manager = PortfolioManager(event_bus, starting_usdc=1000)
    telegram_notifier = TelegramNotifier(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        price_stream.run(),
        candel_snapshot_history.run(),
        candel_stream.run(),
        indicator_swing_detector.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
