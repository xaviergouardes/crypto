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

    def _send_message(self, message: str):       
        """Envoie un message Telegram."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=payload, timeout=5)
        except Exception as e:
            print(f"⚠️ Erreur envoi Telegram : {e}")

    def notify(self, df: pd.DataFrame):

        last_trade = df.iloc[-1].to_dict()
        position = last_trade["position"]
        
        if position and position in ["CLOSE_BUY_TP", "CLOSE_SELL_TP", "CLOSE_BUY_SL", "CLOSE_SELL_SL"]:

            program_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
            pnl = last_trade["trade_pnl"]
            win_loose = "🟢" if pnl >= 0 else "🔴"
            solde = last_trade["capital"]
            side = "BUY" if "BUY" in position else "SELL" if "SELL" in position else None

            msg = (
                f"{program_name} — {win_loose} "
                f"{side} | PnL: {pnl:.2f} | Solde: {solde:.2f} USDC"
            )

            self._send_message(msg)

        return df
 

            
