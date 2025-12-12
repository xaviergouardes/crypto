from trading_bot.system_trading.ma_cross_fast_slow_system_trading import MaCrossFastSlowSystemTrading
from trading_bot.system_trading.random_system_trading import RandomSystemTrading
from trading_bot.system_trading.simple_sweep_system_trading import SimpleSweepSystemTrading

# --- Config globale par bot ---
BOTS_CONFIG = {
    "random_bot": {
        "system_class": RandomSystemTrading,
        "default_parameters": {
            "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
            "symbol": "ethusdc",
            "interval": "1m",
            "initial_capital": 1000,
            "trading_system": {
                "warmup_count": 5,
                "initial_capital": 1000,
                "tp_pct": 0.05,
                "sl_pct": 0.025
            }
        },
        "warmup_attributs": ["warmup_count"]
    },
    "sweep_bot": {
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
    },
    "ma_cross_fast_slow_bot": {
        "system_class": MaCrossFastSlowSystemTrading,
        "default_parameters": {
            "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
            "symbol": "ethusdc",
            "interval": "5m",
            "initial_capital": 1000,
            "trading_system": {
                "fast_period": 14,
                "slow_period": 50,
                "min_gap": 0.01,
                "slope_threshold": 0.01,
                "tp_pct": 1.5,
                "sl_pct": 1.5
            }
        },
        "warmup_attributs": ["slow_period"]
    }
}

__all__ = ["Bot", "BOTS_CONFIG"]