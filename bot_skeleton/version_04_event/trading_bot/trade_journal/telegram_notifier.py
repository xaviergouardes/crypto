import subprocess
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo 

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose, NewSoldes

class TelegramNotifier:
    """
    Envoie une notification Telegram quand un trade se ferme et que le solde a été mis à jour.
    """
    logger = Logger.get("TelegramNotifier")

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.token = "8112934779:AAHwOejwOxsPd5bryocGXDbilwR7tH1hbiA"
        self.chat_id = "6070936106"
        self._running = False

        # Pour synchroniser les événements
        self.message_data = {
            "program_name": os.path.splitext(os.path.basename(sys.argv[0]))[0],
            "gagne_perdu": None,
            "solde": None,
            "side": None,
            "pnl": None
        }

        self.logger.info(f"Initialisé  - {self.token}")

    async def on_new_soldes(self, event: NewSoldes):
        """Reçoit la mise à jour du solde."""
        self.message_data["solde"] = event.usdc
        await self.try_send_message()

    async def on_trade_close(self, event: TradeClose):
        """Reçoit la clôture du trade."""
        # Calcul du PnL (simplifié)
        if event.target == "TP":
            close_price = event.tp
        elif event.target == "SL":
            close_price = event.sl
        else:
            close_price = event.price.price

        pnl = 0.0
        if event.side == "BUY":
            pnl = (close_price - event.price.price) * event.size
        elif event.side == "SELL":
            pnl = (event.price.price - close_price) * event.size

        self.message_data["pnl"] = pnl
        self.message_data["gagne_perdu"] = "🟢" if pnl >= 0 else "🔴"
        self.message_data["side"] = event.side

        await self.try_send_message()

    async def try_send_message(self):
        """Vérifie si on a reçu à la fois TradeClose et NewSoldes."""
        data = self.message_data
        if data["solde"] is not None and data["pnl"] is not None:
            # Construire le message
            message = (
                f"{data['program_name']} — {data['gagne_perdu']} "
                f"{data['side']} | PnL: {data['pnl']:.2f} | Solde: {data['solde']:.2f} USDC"
            )
            self.send_message(message)
            self.reset_message_data()

    def reset_message_data(self):
        """Réinitialise le buffer pour le prochain trade."""
        self.message_data.update({
            "gagne_perdu": None,
            "solde": None,
            "side": None,
            "pnl": None
        })

    def send_message(self, text: str):
        """Envoie le message Telegram via curl sans afficher la sortie."""
        cmd = [
            "curl", "-s", "-X", "POST",
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            "-d", f"chat_id={self.chat_id}",
            "-d", f"text={text}"
        ]
        # -s (silent) est déjà là mais on peut aussi capturer stdout/stderr
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        self.logger.debug(f"Telegram response: {result.stdout}")

    def start(self):
        """Active les écouteurs."""
        if not self._running:
            self.event_bus.subscribe(TradeClose, self.on_trade_close)
            self.event_bus.subscribe(NewSoldes, self.on_new_soldes)
            self._running = True
            self.logger.info("Started...")

    def stop(self):
        """Désactive les écouteurs."""
        if self._running:
            self.event_bus.unsubscribe(TradeClose, self.on_trade_close)
            self.event_bus.unsubscribe(NewSoldes, self.on_new_soldes)
            self._running = False
            self.logger.info("Stopped.")
