from trading_bot.system_trading.random_system_trading import RandomSystemTrading

BOT_NAME = "random_bot"

# --- Config globale par bot ---
BOT_CONFIG =  {
    "system_class": RandomSystemTrading,
    "default_parameters": {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "1m",
        "initial_capital": 1000,
        "trading_system": {
            "filter": False,
            "warmup_count": 5,
            "initial_capital": 1000,
            "tp_pct": 0.05,
            "sl_pct": 0.025
        }
    },
     "warmup_rules": {
        "warmup_count": 1
    }
},