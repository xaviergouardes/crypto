from binance_client import BinanceClient
from decimal import Decimal
from paire import Paire
from mock_paire import MockPaire
from arbitrage_scanner import ArbitrageScanner
from order_engine import OrderEngine
import time
import json
from datetime import datetime
import logging
import logging.config
import yaml
from pathlib import Path

logger = logging.getLogger("bot_trading")

class BotTrading:
    def __init__(self, usdc1: Paire, inter: Paire, usdc2: Paire, capital: Decimal = Decimal("100"), seuilUsdc: Decimal = Decimal("1")):
        
        self.scanner = ArbitrageScanner(usdc1, inter, usdc2, capital=capital, seuilUsdc=seuilUsdc)
        self.order_engine = OrderEngine(usdc1, inter, usdc2, capital=capital)
        self.capital = capital

    def scan_and_trade(self, iterations: int | None = None):
            """Boucle principale : scruter le marché et simuler les trades ALLER uniquement."""
            logger.info("Demarrage du scan_and_trade...")
            count = 0
            while iterations is None or count < iterations:
                try:
                    signal_data = self.scanner.scan()
                    signal = signal_data["signal"]
                    sens = signal_data["sens"]
                    if logger.isEnabledFor(logging.DEBUG): logger.debug(f"signal = {signal_data}")

                    orders = []
                    if signal and sens == "ALLER":
                        if logger.isEnabledFor(logging.DEBUG): logger.debug("Trade ALLER lancé ... ")
                        orders = self.order_engine.execute_trade_aller()

                    if signal and sens == "RETOUR":
                        if logger.isEnabledFor(logging.DEBUG): logger.debug("Trade RETOUR lancé ... ")
                        orders = self.order_engine.execute_trade_retour()

                    result = {
                        "signal_data": signal_data,
                        "orders": orders
                    }
                    if orders:
                        usdc_depart = float(orders[0]["origQuoteOrderQty"])
                        usdc_arrivee = float(orders[2]["cummulativeQuoteQty"])
                        real_profit = usdc_arrivee - usdc_depart
                        logger.info(f"Trade {sens} Real profit {real_profit:.2f} : {json.dumps(result, ensure_ascii=False)}" )

                    if (count + 1) % 20 == 0:
                        logger.info(f"Signal {signal} : {json.dumps(result, ensure_ascii=False)}" )

                    time.sleep(5)
                    count += 1

                except Exception as e:
                    logger.error("Erreur dans le scan_and_trade :", e)
                    raise e
                    time.sleep(5)
            




    def scan_only(self, iterations: int | None = None):
            """Boucle principale : scruter le marché et simuler les trades ALLER uniquement."""
            count = 0
            while iterations is None or count < iterations:
                try:
                    
                    signal_data = self.scanner.scan()
                    time.sleep(5)
                    count += 1

                except Exception as e:
                    logger.error("Erreur dans le scan_only ", e)
                    raise e
                    time.sleep(5)
            
                if logger.isEnabledFor(logging.DEBUG): logger.debug(json.dumps(signal_data, ensure_ascii=False))


    def setup_logging(config_path="logging.yaml"):
        current_dir = Path.cwd()
        config_file = current_dir / "logging.yaml"
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)

if __name__ == "__main__":

    # PAIRS = ["SKLUSDC", "SKLBTC", "BTCUSDC"]
    with BinanceClient(testnet=True) as binance:
        # paires = ["ACHUSDC", "ACHBTC", "BTCUSDC"]
        # paires = ['SKLUSDC', 'SKLBTC', 'BTCUSDC']
        # paires = ['BNBUSDC', 'DOTBNB', 'DOTUSDC']
        # paires = ['BTCUSDC', 'DOTBTC', 'DOTUSDC']
        # paires = ['TRXUSDC', 'TRXBTC', 'BTCUSDC']
        # paires = ['ATOMUSDC', 'ATOMBTC', 'BTCUSDC']
        # paires = ['SOLUSDC', 'SOLETH', 'ETHUSDC']
        # paires = ['AVAXUSDC', 'AVAXBTC', 'BTCUSDC']
        # paires = ['ROSEUSDC', 'ROSEBTC', 'BTCUSDC']
        paires = ['ETHUSDC', 'ETHBTC', 'BTCUSDC']

        p1 = Paire(binance.client, paires[0])
        p2 = Paire(binance.client, paires[1])
        p3 = Paire(binance.client, paires[2])

        #p1 = MockPaire(Paire(binance.client, paires[0]))
        #p2 = MockPaire(Paire(binance.client, paires[1]))
        #p3 = MockPaire(Paire(binance.client, paires[2]))

        bot = BotTrading(p1, p2, p3, 500, 0.1)
        bot.setup_logging()

        result = bot.scan_and_trade()
        #bot.scan_only()