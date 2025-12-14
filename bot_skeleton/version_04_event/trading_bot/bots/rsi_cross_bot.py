from trading_bot.system_trading.rsi_cross_system_trading import RSICrossSystemTrading

BOT_NAME = "rsi_cross_bot"

# --- Config globale par bot ---
BOT_CONFIG = {
    "system_class": RSICrossSystemTrading,
    "default_parameters": {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "5m",
        "initial_capital": 1000,
        "trading_system": {
            "filter": False,
            "rsi_fast_period": 5,
            "rsi_slow_period": 21,
            "atr_period":14,
            "tp_pct": 2,
            "sl_pct": 1
        }
    },
    "warmup_rules": {
        "atr_period": 3
    }
}