/* ======================================= */
curl -X POST "http://127.0.0.1:9101/shutdown" \
    -H "Content-Type: application/json" \
   | jq

/* ======================================= */
curl -X POST "http://127.0.0.1:9101/backtest" \
    -H "Content-Type: application/json" \
    -d '
{
  "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
  "symbol": "ethusdc",
  "interval": "5m",
  "initial_capital": 1000,
  "trading_system": {
    "swing_window": 21,
    "swing_side": 2,
    "tp_pct": 1.5,
    "sl_pct": 1.0
  }
}' | jq

/* ======================================= */
curl -X POST "http://127.0.0.1:9101/backtest" \
    -H "Content-Type: application/json" \
    -d '
{
  "trading_system": {
    "swing_window": 50,
    "tp_pct": 2.5,
    "sl_pct": 0.8
  }
}' | jq

/* ======================================= */
curl -X POST "http://127.0.0.1:9101/train" \
    -H "Content-Type: application/json" \
    -d '
{
  "trading_system": {
    "swing_window": [21, 50],
    "tp_pct": [2.5],
    "sl_pct": [0.8]
  }
}' | jq
