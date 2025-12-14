from trading_bot.system_trading.ma_cross_fast_slow_system_trading import MaCrossFastSlowSystemTrading

BOT_NAME = "ma_cross_bot"

# --- Config globale par bot ---
BOT_CONFIG =  {
    "system_class": MaCrossFastSlowSystemTrading,
    "default_parameters": {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "5m",
        "initial_capital": 1000,
        "trading_system": {
            "filter": False,
            "fast_period": 50,
            "slow_period": 150,
            "min_gap": 1,
            "slope_threshold": 0.5,
            "tp_pct": 2,
            "sl_pct": 1
        }
    },
    "warmup_rules": {
        "slow_period": 1
    }
}