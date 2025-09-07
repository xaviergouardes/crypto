(venv) xavier@localhost-live:~/Documents/gogs-repository/crypto$ /home/xavier/Documents/gogs-repository/crypto/venv/bin/python /home/xavier/Documents/gogs-repository/crypto/arbitrage-ces-sur-triple-paires-binance/mainnet/ordre-achat-vente/bot_trading.py
Erreur lors de la vente MARKET: APIError(code=-2010): Account has insufficient balance for requested action.
Erreur dans execute_trade_aller : order2 'NoneType' object is not subscriptable
Erreur dans le scan/trade: 'NoneType' object is not subscriptable
Traceback (most recent call last):
  File "/home/xavier/Documents/gogs-repository/crypto/arbitrage-ces-sur-triple-paires-binance/mainnet/ordre-achat-vente/bot_trading.py", line 97, in <module>
    result = bot.scan_and_trade(1)
  File "/home/xavier/Documents/gogs-repository/crypto/arbitrage-ces-sur-triple-paires-binance/mainnet/ordre-achat-vente/bot_trading.py", line 40, in scan_and_trade
    raise e
  File "/home/xavier/Documents/gogs-repository/crypto/arbitrage-ces-sur-triple-paires-binance/mainnet/ordre-achat-vente/bot_trading.py", line 33, in scan_and_trade
    orders = self.order_engine.execute_trade_retour()
  File "/home/xavier/Documents/gogs-repository/crypto/arbitrage-ces-sur-triple-paires-binance/mainnet/ordre-achat-vente/order_engine.py", line 66, in execute_trade_retour
    raise e
  File "/home/xavier/Documents/gogs-repository/crypto/arbitrage-ces-sur-triple-paires-binance/mainnet/ordre-achat-vente/order_engine.py", line 63, in execute_trade_retour
    final_usdc = Decimal(order3["cummulativeQuoteQty"])
                         ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable