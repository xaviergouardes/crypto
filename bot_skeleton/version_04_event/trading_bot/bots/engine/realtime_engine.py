import asyncio
from typing import override
import pandas as pd

from trading_bot.core.event_bus import EventBus

from trading_bot.market_data.candle_source_binance import CandleSourceBinance
from trading_bot.bots.engine.engine import Engine
from trading_bot.system_trading.system import System

from trading_bot.trade_journal.telegram_notifier import TelegramNotifier

class RealTimeEngine():
      
    def __init__(self, event_bus:EventBus, system: System, params: dict):

        self._event_bus =  event_bus
        self._params = params
        self._system = system

        # Priorité au warmup_count fourni dans les params
        # self.params = self.system.compute_warmup_count()

        self._candle_source = CandleSourceBinance(self._event_bus, self._params) 
        self._telegram_notifier = TelegramNotifier(self._event_bus)

    @override
    async def run(self):

        # Démarre le pipeline
        self._system.start_piepline()

        # Démarre le notifier Telegram
        self._telegram_notifier.start()

        # Récup warmup
        await self._candle_source.warmup()

        # Lancer le stream dans une tâche concurrente
        await self._candle_source.stream()

    @override
    def stop(self):
        pass
        # Ajouter code pour arrêter proprement le candle_source si nécessaire

    @override
    def get_stats(self) -> dict:
        # Exemple simple : récupérer le journal des trades
        trades = self._system.trader_journal.trades
        df = pd.DataFrame(trades)
        return {
            "num_trades": len(df),
            "total_profit": df['pnl'].sum() if not df.empty else 0,
            "win_rate": len(df[df['pnl'] > 0]) / len(df) if len(df) > 0 else 0
        }
