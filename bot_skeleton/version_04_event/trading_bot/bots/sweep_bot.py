from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

BOT_NAME = "sweep_bot"

# --- Config globale par bot ---
BOT_CONFIG =  {
    "system_class": SimpleSweepSystemTrading,
    "default_parameters": {
        "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
        "symbol": "ethusdc",
        "interval": "5m",
        "initial_capital": 1000,
        "trading_system": {
            "swing_window": 21,
            "swing_side": 2,
            "tp_pct": 1.5,
            "sl_pct": 1.5
        }
    },
    "warmup_attributs": ["swing_window"]
}