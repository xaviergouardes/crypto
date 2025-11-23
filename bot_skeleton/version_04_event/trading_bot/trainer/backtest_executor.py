
import asyncio

from trading_bot.core.logger import Logger

from trading_bot.engine.backtest_engine import BacktestEngine

class BacktestExecutor:

    logger = Logger.get("BacktestExecutor")

    def __init__(self, bot):
        self.bot = bot
        self.default_params = bot.params  # snapshot de référence

    async def execute(self, params: dict | None = None):
 
        # Sélection des paramètres
        if params is None:
            params = self.default_params
        else:
            # Mettre à jour le bot temporairement pour refléter ces paramètres
            self.bot.params = params

        # Recalcul du warmup
        params = self.bot.system_trading.compute_warmup_count()

        self.logger.debug(f"Backtest avec params={params}")

        stats = await self.bot.backtest(params)
        return stats


if __name__ == "__main__":

    import logging
    from trading_bot.bots.sweep_bot import SweepBot

    Logger.set_default_level(logging.INFO)

    # Niveau spécifique pour
    # Logger.set_level("BotTrainer", logging.INFO)
    # Logger.set_level("PortfolioManager", logging.DEBUG)
    # Logger.set_level("TradeJournal", logging.DEBUG)
    
    params = {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "5m",
        "initial_capital": 1000,
        "swing_window": 33,
        "swing_side": 2,
        "tp_pct": 2,
        "sl_pct": 0.5
    }

    bot = SweepBot(params)
    backtest_executor = BacktestExecutor(bot)
    stats = asyncio.run(backtest_executor.execute()) 

    # self.engine = BacktestEngine(self.event_bus, self.system_trading, self.params)
    # stats = await self.engine.run()
    BacktestExecutor.logger.info(f"Statistiques : {stats}")

 