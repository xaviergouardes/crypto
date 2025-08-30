import time
from decimal import Decimal
from UniswapV3Pool import UniswapV3Pool  # Classe existante pour Uniswap V3
from QuickSwapPool import QuickSwapPool  # Classe existante pour QuickSwap

class ArbitrageMonitor:
    def __init__(self):
        self.uniswap_pool = UniswapV3Pool()
        self.quickswap_pool = QuickSwapPool()

    def display_prices(self):
        """Lit les prix et affiche sur une seule ligne avec la différence"""
        price_uni = self.uniswap_pool.get_price()
        price_quick = self.quickswap_pool.get_price()
        
        diff = price_uni - price_quick
        diff_percent = (diff / price_uni * 100) if price_uni != 0 else Decimal(0)

        print(
            f"Prix Uniswap: {price_uni:.2f} | "
            f"Prix QuickSwap: {price_quick:.2f} | "
            f"Différence: {diff:.2f} ({diff_percent:.4f}%)"
        )

def main():
    monitor = ArbitrageMonitor()
    while True:
        try:
            monitor.display_prices()
            time.sleep(10)
        except KeyboardInterrupt:
            print("Arrêt du monitoring...")
            break
        except Exception as e:
            print("Erreur :", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
