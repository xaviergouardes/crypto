import aiohttp

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeClose, NewSoldes
from trading_bot.core.startable import Startable


class TelegramNotifier(Startable):
    logger = Logger.get("TelegramNotifier")

    def __init__(self, event_bus: EventBus, params: dict):
        super().__init__()

        self.event_bus = event_bus

        self.token = "8112934779:AAHwOejwOxsPd5bryocGXDbilwR7tH1hbiA"
        self.chat_id = "6070936106"

        self.program_name = params["bot_id"]

        self._session: aiohttp.ClientSession | None = None

        self._message_data = {
            "solde": None,
            "side": None,
            "pnl": None
        }

        # Subscriptions (safe même si non démarré)
        self.event_bus.subscribe(TradeClose, self._on_trade_close)
        self.event_bus.subscribe(NewSoldes, self._on_new_soldes)

        self.logger.info(f"Initialisé (chat_id={self.chat_id})")

    # ------------------------------------------------------------------
    # Start / Stop lifecycle
    # ------------------------------------------------------------------

    async def _on_start(self):
        self._session = aiohttp.ClientSession()
        self.logger.info("📨 TelegramNotifier démarré (session HTTP ouverte)")

    def _on_stop(self):
        if self._session and not self._session.closed:
            # fermeture propre async → on délègue à l’event loop
            import asyncio
            asyncio.create_task(self._session.close())

        self._session = None
        self._reset_message_data()

        self.logger.info("🛑 TelegramNotifier arrêté (session HTTP fermée)")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_new_soldes(self, event: NewSoldes):
        if not self.is_running():
            return

        self._message_data["solde"] = event.usdc
        await self._try_send_message()

    async def _on_trade_close(self, event: TradeClose):
        if not self.is_running():
            return

        self._message_data["pnl"] = event.pnl
        self._message_data["side"] = event.side
        await self._try_send_message()

    # ------------------------------------------------------------------
    # Message logic
    # ------------------------------------------------------------------

    async def _try_send_message(self):
        if not self._session:
            return

        data = self._message_data
        if data["solde"] is None or data["pnl"] is None:
            self.logger.debug("TelegramNotifier: données incomplètes")
            return

        gagne_perdu = "🟢" if data["pnl"] >= 0 else "🔴"

        message = (
            f"{self.program_name} — {gagne_perdu} "
            f"{data['side']} | PnL: {data['pnl']:.2f} | "
            f"Solde: {data['solde']:.2f} USDC"
        )

        try:
            await self._send_message(message)
            self.logger.debug("Message Telegram envoyé")
        except Exception as e:
            self.logger.error("Erreur en envoyant Telegram: %r", e)
        finally:
            self._reset_message_data()

    def _reset_message_data(self):
        self._message_data.update({
            "solde": None,
            "side": None,
            "pnl": None
        })

    # ------------------------------------------------------------------
    # Telegram API
    # ------------------------------------------------------------------

    async def _send_message(self, text: str):
        assert self._session is not None

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text
        }

        async with self._session.post(url, data=payload, timeout=10) as resp:
            body = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Telegram error {resp.status}: {body}")
