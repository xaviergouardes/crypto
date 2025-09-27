# trading_bot/main.py
import asyncio

from trading_bot.core.event_bus import EventBus

from trading_bot.market_data.order_book_stream import OrderBookStream
from trading_bot.market_data.price_stream import PriceStream
from trading_bot.order_book_analyzer.order_book_analyzer import OrderBookAnalyzer
from trading_bot.indicator_engine.indicator_engine import IndicatorEngine
from trading_bot.strategy.strategy_smacross import StrategySmaCrossEngine
from trading_bot.risk_manager.risk_manager import RiskManager
from trading_bot.trader.trader_only_one_position import TraderOnlyOnePosition
from trading_bot.trade_journal.trade_journal import TradeJournal


async def main():
    event_bus = EventBus()

    # Initialisation des modules
    price_stream = PriceStream(event_bus)               # récupère les prix 
    order_book_stream = OrderBookStream(event_bus)      # et carnet réel
    order_book_analyzer = OrderBookAnalyzer(event_bus)  # analyse supports/résistances
    indicator_engine = IndicatorEngine(event_bus)       # calcule indicateurs
    strategy_engine = StrategySmaCrossEngine(event_bus)         # génère les signaux
    risk_manager = RiskManager(event_bus, tp_percent=0.02, sl_percent=0.02)
    trader = TraderOnlyOnePosition(event_bus)
    trader_journal = TradeJournal(event_bus)

    # Lancer tous les modules
    await asyncio.gather(
        price_stream.run(),
        order_book_stream.run(),
        order_book_analyzer.run(),
        indicator_engine.run(),
        strategy_engine.run(),
        risk_manager.run(),
        trader.run(),
        trader_journal.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
