# trading_bot/core/events.py
from dataclasses import dataclass
from typing import List, Tuple
from .event_bus import Event
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# Une structure de type Chandelier
@dataclass
class Candle(Event):
    index:int
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    start_time: datetime
    end_time: datetime

    def __str__(self):
        # Conversion UTC → Paris
        paris_tz = ZoneInfo("Europe/Paris")
        start_paris = self.start_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(paris_tz)
        end_paris = self.end_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(paris_tz)

        return (f"Candle({self.symbol}) | {self.index} | "
                f"o: {self.open:.2f}, h: {self.high:.2f}, l: {self.low:.2f}, c: {self.close:.2f}, "
                f"v: {self.volume:.3f} | "
                f"{start_paris:%Y-%m-%d %H:%M:%S} / {end_paris:%Y-%m-%d %H:%M:%S})")
    
    def is_next_of(self, other: "Candle") -> bool:
        """
        Retourne True si self est la bougie N+1 par rapport à other
        """
        return self.index == other.index + 1

    def is_previous_of(self, other: "Candle") -> bool:
        """
        Retourne True si self est la bougie N-1 par rapport à other
        """
        return self.index == other.index - 1


# 🪟 Événement : carnet d’ordre mis à jour
@dataclass
class OrderBookUpdated(Event):
    symbol: str
    bids: List[Tuple[float, float]]
    asks: List[Tuple[float, float]]

# 📊 Support / résistance détectés
@dataclass
class SupportResistanceDetected(Event):
    supports: List[float]      # Liste de niveaux de support
    resistances: List[float]   # Liste de niveaux de résistance

# 📉 Indicateur technique généré
@dataclass
class IndicatorUpdated(Event):
    """Événement publié lorsque les indicateurs sont recalculés."""
    symbol: str
    candle: Candle
    values: dict 

# 📊 Signal de stratégie
@dataclass
class TradeSignalGenerated(Event):
    side: str
    confidence: float
    candle: Candle
    strategie: str
    strategie_parameters: dict
    strategie_values: dict
    filtred: bool = False

    def mark_filtered(self, reason: str | None = None):
        self.filtred = True
        if reason:
            self.strategie_values["filter_reason"] = reason


# ✅ Trade validé par le Risk Manager
@dataclass
class TradeApproved(Event):
    side: str
    size: float
    candle: Candle
    tp: float
    sl: float

# Trade Close par le Trader
@dataclass
class TradeClose(Event):
    side: str
    size: float
    candle_open: Candle
    candle_close: Candle
    tp: float
    sl: float
    target: str # TP / SL

    @property
    def entry_price(self) -> float:
        return self.candle_open.close
    
    @property
    def exit_price(self) -> float:
        if self.target == "TP": return self.tp
        if self.target == "SL": return self.sl
        return None
    
    @property
    def pnl(self) -> float:
        """
        PnL brut (sans spread / commission)
        """
        pnl = None
        if self.side == "BUY":
            pnl = (self.exit_price - self.entry_price) * self.size
            # print(f"==> BUY => pnl={pnl} | exit_price={self.exit_price},  entry_price={self.entry_price}, size={self.size}")
        elif self.side == "SELL":
            pnl = (self.entry_price - self.exit_price) * self.size
            # print(f"==> SELL => pnl={pnl} | exit_price={self.exit_price},  entry_price={self.entry_price}, size={self.size}")
        else:
            raise ValueError(f"Side inconnu : {self.side}")
        return pnl
    

# ❌ Trade rejeté
@dataclass
class TradeRejected(Event):
    reason: str

# Event émis a chaque fermeture de bougie
@dataclass
class CandleClose(Event):
    symbol: str
    candle: Candle

# 
@dataclass
class CandleHistoryReady(Event):
    symbol: str
    timestamp: datetime
    period: timedelta
    candles: List[Candle]

# ❌ Trade rejeté
@dataclass
class NewSoldes(Event):
    usdc: float
    eth: float

    