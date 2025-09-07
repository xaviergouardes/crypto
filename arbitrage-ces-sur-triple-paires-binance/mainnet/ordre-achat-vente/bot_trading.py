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
            count = 0
            while iterations is None or count < iterations:
                try:
                    
                    signal_data = self.scanner.scan()
                    signal = signal_data["signal"]
                    sens = signal_data["sens"]

                    orders = []
                    if signal and sens == "ALLER":
                        orders = self.order_engine.execute_trade_aller()

                    if signal and sens == "RETOUR":
                        orders = self.order_engine.execute_trade_retour()

                    time.sleep(5)
                    count += 1

                except Exception as e:
                    print("Erreur dans le scan/trade:", e)
                    raise e
                    time.sleep(5)
            
                result = {
                    "signal_data": signal_data,
                    "orders": orders
                }

                self.log_trade(result)

    def scan_only(self, iterations: int | None = None):
            """Boucle principale : scruter le marché et simuler les trades ALLER uniquement."""
            count = 0
            while iterations is None or count < iterations:
                try:
                    
                    signal_data = self.scanner.scan()
                    time.sleep(5)
                    count += 1

                except Exception as e:
                    print("Erreur dans le scan onlytrade:", e)
                    raise e
                    time.sleep(5)
            
                logger.debug(json.dumps(signal_data, ensure_ascii=False))


    def log_trade(self, result: dict, filename="./trades.json"):
        # Ajoute un horodatage dans les données
        result_with_time = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            **result
        }

        # Écrit dans le fichier en mode append (chaque trade sur une ligne JSON)
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(result_with_time, ensure_ascii=False) + "\n")

        # Affiche joliment à l’écran
        print(json.dumps(result_with_time, ensure_ascii=False))


    def setup_logging(config_path="logging.yaml"):
        current_dir = Path.cwd()
        config_file = current_dir / "logging.yaml"
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)

if __name__ == "__main__":

    logger.info(f"Bot Trading Démarrge ...")

    # PAIRS = ["SKLUSDC", "SKLBTC", "BTCUSDC"]
    with BinanceClient() as binance:
        # paires = ["ACHUSDC", "ACHBTC", "BTCUSDC"]
        paires = ['SKLUSDC', 'SKLBTC', 'BTCUSDC']

        #p1 = Paire(binance.client, paires[0])
        #p2 = Paire(binance.client, paires[1])
        #p3 = Paire(binance.client, paires[2])

        p1 = MockPaire(Paire(binance.client, paires[0]))
        p2 = MockPaire(Paire(binance.client, paires[1]))
        p3 = MockPaire(Paire(binance.client, paires[2]))

        bot = BotTrading(p1, p2, p3, 50, 0.5)
        bot.setup_logging()

        #result = bot.scan_and_trade(1)
        bot.scan_only()