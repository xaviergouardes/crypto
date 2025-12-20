/* ======================================= */
curl -X POST "http://127.0.0.1:9101/server/shutdown" \
    -H "Content-Type: application/json" \
   | jq

/* ======================================= */
curl -X POST "http://127.0.0.1:9101/bot/backtest" \
    -H "Content-Type: application/json" \
    -d '{
  "path": "/home/xavier/Documents/gogs-repository/crypto/bot_skeleton/hitorique_binance/ETHUSDC_5m_historique_20250914_20251114.csv",
  "symbol": "ethusdc",
  "interval": "5m",
  "initial_capital": 1000,
      "trading_system": {
          "ema_period": 200,
          "tp_pct": 2,
          "sl_pct": 1
      }
}' | jq


/* ======================================= */
curl -X POST "http://127.0.0.1:9101/bot/train" \
    -H "Content-Type: application/json" \
    -d '{
        "trading_system": {
            "ema_period": [200],
            "tp_pct": [2],
            "sl_pct": [1]
        }
}' | jq

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
      "ema_period": 200,
      "tp_pct": 2,
      "sl_pct": 1
  }
}' | jq
