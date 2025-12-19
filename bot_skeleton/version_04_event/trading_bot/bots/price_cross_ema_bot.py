from trading_bot.system_trading.price_cross_system_trading import PriceCrossSystemTrading

BOT_NAME = "price_cross_ema_bot"

# --- Config globale par bot ---
BOT_CONFIG =  {
    "system_class": PriceCrossSystemTrading,
    "default_parameters": {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "5m",
        "initial_capital": 1000,
        "trading_system": {
            "ema_period": 200,
            "tp_pct": 2,
            "sl_pct": 1
        }
    },
    "warmup_rules": {
        "ema_period": 1
    }
}
