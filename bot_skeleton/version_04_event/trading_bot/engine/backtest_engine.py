import pandas as pd

from trading_bot.core.event_bus import EventBus

from trading_bot.market_data.candle_source_csv import CandleSourceCsv
from trading_bot.engine.engine import Engine
from trading_bot.system_trading.system import System

class BacktestEngine(Engine):
      
    def __init__(self, event_bus:EventBus, system: System, params: dict):
        self.event_bus =  event_bus
        self.params = params
        self.system = system

        self._running = None

        # # Priorité au warmup_count fourni dans les params
        # Priorité au warmup_count fourni dans les params
        self.params = self.system.compute_warmup_count()

        self.candle_source = CandleSourceCsv(self.event_bus, params) 

    async def run(self):
        pass
        self._running = True
        
        # Démarrer le pipeline pour que les composants puissent capturer les events
        self.system.start_piepline()

        # Lancer la récupéreration des bougie de warnup
        await self.candle_source.warmup()

        # Boucle événementielle -> non bloqunte en backtest
        await self.candle_source.stream() 

        return self.system.trader_journal.summary()

    async def stop(self):
        self._running = False
        # Ajouter code pour arrêter proprement le candle_source si nécessaire

    async def get_stats(self) -> dict:
        pass
        # # Exemple simple : récupérer le journal des trades
        trades = self.system.trader_journal.trades
        df = pd.DataFrame(trades)
        return {
            "num_trades": len(df),
            "total_profit": df['pnl'].sum() if not df.empty else 0,
            "win_rate": len(df[df['pnl'] > 0]) / len(df) if len(df) > 0 else 0
        }
