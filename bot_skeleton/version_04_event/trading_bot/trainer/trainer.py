

from itertools import product
import pandas as pd


class BotTrainer:

    def __init__(self, bot_class, params):
        self.bot = bot_class
        self.params = params

    async def run(self, param_grid):

        # Générer toutes les combinaisons de paramètres variables
        keys, values = zip(*param_grid.items())
        param_combinations = [dict(zip(keys, v)) for v in product(*values)]

        # Fusionner chaque combinaison avec les paramètres fixes
        full_param_sets = []
        for combo in param_combinations:
            full_params = self.params.copy()  # on part des paramètres fixes
            full_params.update(combo)          # on remplace avec les valeurs variables
            full_param_sets.append(full_params)

        results = []
        for params in full_param_sets:

            bot = self.bot(params, "backtest")
            bot.system_trading.compute_warmup_count()
            await bot.run()

            journal = bot.system_trading.trader_journal.trades
            df_journal = pd.DataFrame(journal)
            
            # Ajouter les paramètres utilisés
            for k, v in params.items():
                df_journal[k] = v
            
            # Metrics simples
            total_profit = df_journal['pnl'].sum() if not df_journal.empty else 0
            win_rate = len(df_journal[df_journal['pnl'] > 0]) / len(df_journal) if len(df_journal) > 0 else 0

            result = {
                'params': params,
                'total_profit': total_profit,
                'win_rate': win_rate,
                'num_trades': len(df_journal),
                'journal': df_journal
            }
            results.append(result)

        # Retourner un DataFrame résumé des performances
        summary = pd.DataFrame([{
            'total_profit': r['total_profit'],
            'win_rate': r['win_rate'],
            'num_trades': r['num_trades'],
            **r['params']
        } for r in results])
        
        return summary
