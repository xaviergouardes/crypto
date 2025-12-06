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
    "swing_window": [21, 50, 75, 100, 200],
    "tp_pct": [0.5, 1, 1.5, 2, 2.5],
    "sl_pct": [0.5, 1, 1.5, 2, 2.5]
  }
}' | jq

/* ======================================= */
curl -X POST "http://127.0.0.1:9101/start" \
    -H "Content-Type: application/json" \
    -d '
{
  "symbol": "ethusdc",
  "interval": "1m",
  "initial_capital": 1000,
  "trading_system": {
    "swing_window": 21,
    "swing_side": 2,
    "tp_pct": 1.5,
    "sl_pct": 1.5
  }
}' | jq

/* ======================================= */
/* ======         Random Bot         ======*/
/* ======================================= */
curl -X POST "http://127.0.0.1:9101/start" \
    -H "Content-Type: application/json" \
    -d '
{
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
}' | jq

curl -X POST "http://127.0.0.1:9101/backtest" \
    -H "Content-Type: application/json" \
    -d '
{
  "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
  "symbol": "ethusdc",
  "interval": "5m",
  "initial_capital": 1000,
  "trading_system": {
      "warmup_count": 5,
      "initial_capital": 1000,
      "tp_pct": 2,
      "sl_pct": 1
  }
}' | jq

curl -X POST "http://127.0.0.1:9101/train" \
    -H "Content-Type: application/json" \
    -d '
{
  "trading_system": {
      "warmup_count": [5],
      "initial_capital": [1000],
      "tp_pct": [2,3],
      "sl_pct": [1,2]
  }
}' | jq