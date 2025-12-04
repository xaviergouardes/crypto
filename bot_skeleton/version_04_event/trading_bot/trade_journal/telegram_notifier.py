import aiohttp

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose, NewSoldes


class TelegramNotifier():
    logger = Logger.get("TelegramNotifier")

    def __init__(self, event_bus: EventBus, params: dict):
        self.event_bus = event_bus

        self.token = "8112934779:AAHwOejwOxsPd5bryocGXDbilwR7tH1hbiA"
        self.chat_id = "6070936106"
        
        self.message_data = {
            "program_name": params["bot_id"],
            "gagne_perdu": None,
            "solde": None,
            "side": None,
            "pnl": None
        }
        self.event_bus.subscribe(TradeClose, self.on_trade_close)
        self.event_bus.subscribe(NewSoldes, self.on_new_soldes)
        # session aiohttp optionnelle, on peut la réutiliser
        self._session = aiohttp.ClientSession()
        self.logger.info("Initialisé")

    async def close(self):
        await self._session.close()

    async def on_new_soldes(self, event: NewSoldes):
        self.message_data["solde"] = event.usdc
        await self.try_send_message()

    async def on_trade_close(self, event: TradeClose):
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
        data = self.message_data
        if data["solde"] is None or data["pnl"] is None:
            # rien à faire, on attend l'autre événement
            self.logger.debug("try_send_message: données incomplètes")
            return

        message = (
            f"{data['program_name']} — {data['gagne_perdu']} "
            f"{data['side']} | PnL: {data['pnl']:.2f} | Solde: {data['solde']:.2f} USDC"
        )

        # Envoie asynchrone
        try:
            await self._send_message_aiohttp(message)
            self.logger.debug("Message Telegram sent: %s", message)
        except Exception as e:
            self.logger.error("Erreur en envoyant Telegram: %r", e)

        self.reset_message_data()

    def reset_message_data(self):
        self.message_data.update({
            "gagne_perdu": None,
            "solde": None,
            "side": None,
            "pnl": None
        })

    async def _send_message_aiohttp(self, text: str):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        # timeout et gestion d'erreurs
        async with self._session.post(url, data=payload, timeout=10) as resp:
            txt = await resp.text()
            self.logger.debug("Telegram response status=%s body=%s", resp.status, txt)
            if resp.status != 200:
                raise RuntimeError(f"TG non-200: {resp.status}")


