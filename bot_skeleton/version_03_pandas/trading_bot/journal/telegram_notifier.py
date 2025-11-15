import requests
import pandas as pd
import os
import sys

class TelegramNotifier:
    """
    Ajoute une colonne 'telegram' au DataFrame et envoie une notification Telegram
    pour chaque trade clôturé (TP/SL) non encore notifié.
    """

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def send_message(self, message: str):
        """Envoie un message Telegram."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=payload, timeout=5)
        except Exception as e:
            print(f"⚠️ Erreur envoi Telegram : {e}")

    def notify(self, trade: dict):
        ts = trade['timestamp_paris']
        close_price = trade.get('trade.sl') if 'SL' in trade['position'] else trade.get('trade.tp')

        msg = (
            f"{os.path.splitext(os.path.basename(sys.argv[0]))[0]} \n"
            f"💰 *Trade clôturé* : {trade['position']}\n"
            f"📅 {ts}\n"
            f"🎯 Entry: {trade['trade.entry_price']:.4f}\n"
            f"💎 Close: {close_price:.4f}\n"
            f"📈 PnL: {trade['trade_pnl']:.2f} USDC\n"
            f"💼 Solde: {trade['capital']:.2f} USDC"
        )
        self.send_message(msg)

