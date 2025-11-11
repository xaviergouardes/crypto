import pandas as pd
from datetime import datetime

from trading_bot.risk_manager.risk_manager import RiskManager
from trading_bot.trader.trader_only_one_position import OnlyOnePositionTrader


# ====== Data simulée ======
data = [
    # Trade 1 - BUY
    {'timestamp': datetime(2025, 9, 1, 15, 55), 'close': 4362.61, 'signal': 'BUY', 'high': 4370, 'low': 4350},
    {'timestamp': datetime(2025, 9, 1, 16, 00), 'close': 4354.90, 'signal': None, 'high': 4360, 'low': 4350},
    {'timestamp': datetime(2025, 9, 1, 16, 5), 'close': 4363.10, 'signal': None, 'high': 4370, 'low': 4355},
    # Trade 2 - SELL
    {'timestamp': datetime(2025, 9, 1, 21, 5), 'close': 4276.71, 'signal': 'SELL', 'high': 4285, 'low': 4270},
    {'timestamp': datetime(2025, 9, 1, 21, 10), 'close': 4272.50, 'signal': None, 'high': 4278, 'low': 4270},
]

df = pd.DataFrame(data)
df.set_index('timestamp', inplace=True)

# ====== Calcul du TP et SL via RiskManager ======
rm = RiskManager(df, tp_pct=5, sl_pct=4)
df = rm.calculate_risk()

# ====== Simulation du trader ======
trader = OnlyOnePositionTrader(df)
result = trader.run_trades()

print(result[['close','signal','entry_price','tp','sl','position','trade_id']])
