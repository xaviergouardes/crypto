# trading_bot/main.py
import asyncio

from trading_bot.core.event_bus import EventBus

from trading_bot.market_data.order_book_stream import OrderBookStream
from trading_bot.market_data.price_stream import PriceStream
from trading_bot.order_book_analyzer.order_book_analyzer import OrderBookAnalyzer
from trading_bot.indicator_engine.indicator_engine import IndicatorEngine
from trading_bot.strategy.strategy import StrategyEngine
from trading_bot.risk_manager.risk_manager import RiskManager
from trading_bot.trader.trader import Trader

async def main():
    event_bus = EventBus()

    # Initialisation des modules
    price_stream = PriceStream(event_bus)               # récupère les prix 
    order_book_stream = OrderBookStream(event_bus)      # et carnet réel
    order_book_analyzer = OrderBookAnalyzer(event_bus)  # analyse supports/résistances
    indicator_engine = IndicatorEngine(event_bus)       # calcule indicateurs
    strategy_engine = StrategyEngine(event_bus)         # génère les signaux
    risk_manager = RiskManager(event_bus, tp_percent=1.0, sl_percent=0.5)
    trader = Trader(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        price_stream.run(),
        order_book_stream.run(),
        order_book_analyzer.run(),
        indicator_engine.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
