curl -s http://127.0.0.1:9101/server/log-level | jq


curl -X POST http://127.0.0.1:9101/server/log-level \
     -H "Content-Type: application/json" \
     -d '{"logger": "Backtest", "level": "DEBUG"}'


curl -X POST http://127.0.0.1:9101/server/log-level \
     -H "Content-Type: application/json" \
     -d '{"logger": "ALL", "level": "DEBUG"}'
