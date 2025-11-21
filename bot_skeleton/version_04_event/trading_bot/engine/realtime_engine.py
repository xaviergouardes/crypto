import asyncio
from typing import override
import pandas as pd

from trading_bot.core.event_bus import EventBus

from trading_bot.market_data.candle_source_binance import CandleSourceBinance
from trading_bot.engine.engine import Engine
from trading_bot.system_trading.system import System

from trading_bot.trade_journal.telegram_notifier import TelegramNotifier

class RealTimeEngine(Engine):
      
    def __init__(self, event_bus:EventBus, system: System, params: dict):
        self.event_bus =  event_bus
        self.params = params
        self.system = system
        
        self._running = None

        # Priorité au warmup_count fourni dans les params
        self.params = self.system.compute_warmup_count()

        self.candle_source = CandleSourceBinance(self.event_bus, self.params) 
        self.telegram_notifier = TelegramNotifier(self.event_bus)

    @override
    async def run(self):
        self._running = True

        # Démarre le pipeline
        self.system.start_piepline()

        # Démarre le notifier Telegram
        self.telegram_notifier.start()

        # Récup warmup
        await self.candle_source.warmup()

        # Lancer le stream dans une tâche concurrente
        await self.candle_source.stream()

    @override
    async def stop(self):
        self._running = False
        # Ajouter code pour arrêter proprement le candle_source si nécessaire

    @override
    async def get_stats(self) -> dict:
        # Exemple simple : récupérer le journal des trades
        trades = self.system.trader_journal.trades
        df = pd.DataFrame(trades)
        return {
            "num_trades": len(df),
            "total_profit": df['pnl'].sum() if not df.empty else 0,
            "win_rate": len(df[df['pnl'] > 0]) / len(df) if len(df) > 0 else 0
        }
