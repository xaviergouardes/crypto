import asyncio
from binance import AsyncClient
from trading_bot.market_data.market_data import MarketData
from trading_bot.market_data.order_book_data import OrderBookData
from trading_bot.order_book_analyzer.order_book_analyzer import OrderBookAnalyzer
from trading_bot.indicator_engine.indicator_engine import IndicatorEngine
from trading_bot.strategy.strategy import Strategy
from trading_bot.risk_manager.risk_manager import RiskManager
from trading_bot.trader.trader import Trader
from trading_bot.protocols.shared_state import SharedState
from trading_bot.protocols.protocols import (
    MarketDataProtocol,
    OrderBookDataProtocol,
    OrderBookAnalyzerProtocol,
    IndicatorEngineProtocol,
    StrategyProtocol,
    RiskManagerProtocol,
    TraderProtocol
)

class TradingBot:
    def __init__(self, api_key, api_secret, symbol="BTCUSDT"):
        self.state = SharedState()
        self.symbol = symbol
        self.api_key = api_key
        self.api_secret = api_secret

    async def run(self):
        client = await AsyncClient.create(self.api_key, self.api_secret)
        market_data = MarketData(self.state, client, self.symbol)
        order_book_data = OrderBookData(self.state, client, self.symbol)
        order_book_analyzer = OrderBookAnalyzer(self.state)
        indicator = IndicatorEngine(self.state)
        strategy = Strategy(self.state)
        risk_manager = RiskManager(self.state)
        trader = Trader(self.state)

        await asyncio.gather(
            market_data.run(),
            order_book_data.run(),
            order_book_analyzer.run(),
            indicator.run(),
            strategy.run(),
            risk_manager.run(),
            trader.run()
        )
