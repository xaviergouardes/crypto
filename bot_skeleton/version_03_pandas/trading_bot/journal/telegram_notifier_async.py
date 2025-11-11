import aiohttp
import pandas as pd
import asyncio
import os
import sys

class AsyncTelegramNotifier:
    """
    Version asynchrone du notifier Telegram.
    Ajoute une colonne 'telegram' au DataFrame et envoie un message pour chaque trade clôturé non notifié.
    """

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    async def send_message(self, session: aiohttp.ClientSession, message: str):
        """Envoie un message Telegram de manière asynchrone."""
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            async with session.post(self.api_url, data=payload, timeout=5) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"⚠️ Erreur Telegram ({resp.status}) : {text}")
        except Exception as e:
            print(f"⚠️ Erreur envoi Telegram : {e}")

    async def notify(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parcourt le DataFrame et envoie un message pour les trades clôturés non notifiés.
        Retourne le DataFrame mis à jour avec la colonne 'telegram'.
        """
        df = df.copy()

        if 'telegram' not in df.columns:
            df['telegram'] = False

        # Sélectionne les trades clôturés non encore notifiés
        mask = (
            df['position'].isin(['CLOSE_BUY_TP', 'CLOSE_BUY_SL', 'CLOSE_SELL_TP', 'CLOSE_SELL_SL'])
            & (df['telegram'] == False)
        )
        closed_trades = df[mask]

        if closed_trades.empty:
            return df

        async with aiohttp.ClientSession() as session:
            tasks = []

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

                # Création d'une tâche asynchrone
                tasks.append(self.send_message(session, msg))
                df.at[i, 'telegram'] = True  # Marque la ligne comme notifiée

            # Envoi concurrent des messages Telegram
            await asyncio.gather(*tasks)

        return df


"""
df = Portfolio(df, initial_capital=self.initial_capital).run_portfolio()
notifier = AsyncTelegramNotifier(token=BOT_TOKEN, chat_id=CHAT_ID)
df = asyncio.run(notifier.notify(df))
"""