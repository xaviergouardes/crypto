from dataclasses import dataclass
from enum import Enum
from typing import Optional

from trading_bot.core.events import Candle


class TradeState(Enum):
    OPEN = "open"                 # signal créé / ordre en attente
    IN_POSITION = "in_position"   # position exécutée
    CLOSED = "closed"             # trade terminé


@dataclass
class Trade:
    # --- Identification / intention ---
    side: str                     # "buy" | "sell"
    size: float
    target: Optional[str] = None

    # --- Prix ---
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    tp: Optional[float] = None
    sl: Optional[float] = None

    # --- Temps ---
    open_timestamp: Optional[float] = None
    close_timestamp: Optional[float] = None

    # --- Contexte marché ---
    candle_open: Optional[Candle] = None
    candle_close: Optional[Candle] = None

    # --- Résultat ---
    pnl: Optional[float] = None

    # --- État ---
    state: TradeState = TradeState.OPEN

    # ======================================================
    # =============== MÉTHODES MÉTIER ======================
    # ======================================================
    def _exit_price(self, target:str) -> float:
        if target == "TP": return self.tp
        if target == "SL": return self.sl
        return None
    
    def enter_position(self):
        """
        Passe le trade de OPEN -> IN_POSITION
        """
        if self.state != TradeState.OPEN:
            raise RuntimeError("Trade must be OPEN to enter position")

        self.state = TradeState.IN_POSITION

    def close(self, target: str, candle_close: Candle):
        """
        Passe le trade de IN_POSITION -> CLOSED
        """
        if self.state != TradeState.IN_POSITION:
            raise RuntimeError("Trade must be IN_POSITION to be closed")

        self.exit_price = self._exit_price(target)
        self.candle_close = candle_close
        self.close_timestamp = candle_close.end_time

        self.pnl = self._compute_pnl(self.exit_price)

        self.state = TradeState.CLOSED

    # ======================================================
    # ================= LOGIQUE PURE =======================
    # ======================================================

    def _compute_pnl(self, exit_price: float) -> float:
        if self.entry_price is None:
            raise RuntimeError("entry_price is not set")

        if self.side == "BUY":
            return (exit_price - self.entry_price) * self.size
        elif self.side == "SELL":
            return (self.entry_price - exit_price) * self.size
        else:
            raise ValueError(f"Invalid side: {self.side}")

    # ======================================================
    # ================= PROPRIÉTÉS =========================
    # ======================================================

    @property
    def is_open(self) -> bool:
        return self.state == TradeState.OPEN

    @property
    def is_in_position(self) -> bool:
        return self.state == TradeState.IN_POSITION

    @property
    def is_closed(self) -> bool:
        return self.state == TradeState.CLOSED


    def __str__(self) -> str:
        if self.state == TradeState.OPEN or self.state == TradeState.IN_POSITION:
            return (
                f"[TRADE | {self.state}] "
                f"side={self.side} "
                f"size={self.size} "
                f"entry={self.entry_price} "
                f"tp={self.tp} "
                f"sl={self.sl} "
                f"opened_at={self.open_timestamp}"
            )

        if self.state == TradeState.CLOSED:
            return (
                f"[TRADE | CLOSED] "
                f"target={self.target} "
                f"side={self.side} "
                f"entry={self.entry_price} "
                f"exit={self.exit_price} "
                f"tp={self.tp} "
                f"sl={self.sl} "
                f"size={self.size} "
                f"pnl={round(self.pnl, 2) if self.pnl is not None else None} "
                f"opened_at={self.open_timestamp} "
                f"closed_at={self.close_timestamp}"
            )

        return "[TRADE | UNKNOWN STATE]"
