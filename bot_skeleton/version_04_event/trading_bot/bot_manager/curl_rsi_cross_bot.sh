/* ======================================= */
curl -X POST "http://127.0.0.1:9101/bot/start" \
    -H "Content-Type: application/json" \
    -d '
{
    "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
    "symbol": "ethusdc",
    "interval": "5m",
    "initial_capital": 1000,
    "trading_system": {
        "atr_filter": true,
        "rsi_fast_period": 15,
        "rsi_slow_period": 100,
        "atr_period":90,
        "tp_pct": 1.5,
        "sl_pct": 1.5
    }
}' | jq
