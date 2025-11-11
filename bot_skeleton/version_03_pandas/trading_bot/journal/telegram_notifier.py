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

    def notify(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parcourt le DataFrame et envoie un message pour les trades clôturés non notifiés.
        Retourne le DataFrame mis à jour avec la colonne 'telegram'.
        """
        df = df.copy()

        if 'telegram' not in df.columns:
            df['telegram'] = False

        # Sélectionne uniquement les trades clôturés non encore notifiés
        mask = (
            df['position'].isin(['CLOSE_BUY_TP', 'CLOSE_BUY_SL', 'CLOSE_SELL_TP', 'CLOSE_SELL_SL'])
            & (df['telegram'] == False)
        )
        closed_trades = df[mask]

        for i, row in closed_trades.iterrows():
            ts = row.get('timestamp_paris', row['timestamp'])
            msg = (
                f"{os.path.splitext(os.path.basename(sys.argv[0]))[0]} \n"
                f"💰 *Trade clôturé* : {row['position']}\n"
                f"📅 {ts}\n"
                f"🎯 Entry: {row['entry_price']:.4f}\n"
                f"💎 Close: {row['close']:.4f}\n"
                f"📈 PnL: {row['trade_pnl']:.2f} USDC\n"
                f"💼 Solde: {row['capital']:.2f} USDC"
            )
            self.send_message(msg)
            df.at[i, 'telegram'] = True  # Marque le trade comme notifié

        return df
