

from trading_bot.data_market.candle_source_csv import CandleSourceCsv

from trading_bot.systems.system_abstract import System


class BacktestEngine:

    def __init__(self, system: System, path: str):

        self.system = system
        self.candle_source = CandleSourceCsv(path)        

    def run(self):

        # On charge tout le CSV pour le backtest
        df = self.candle_source.get_initial_data().copy()

        df, stats = self.system.run(df)

        print(stats.summary())
