# trading_bot/core/events.py
from dataclasses import dataclass
from typing import List, Tuple
from .event_bus import Event

# 📈 Événement : nouveau prix reçu
@dataclass
class PriceUpdated(Event):
    symbol: str
    price: float

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
class IndicatorUpdated:
    """Événement publié lorsque les indicateurs sont recalculés."""
    def __init__(self, values: dict):
        self.values = values  # ex: {"sma": 123.45, "momentum": 0.67}

# 📊 Signal de stratégie
@dataclass
class TradeSignalGenerated(Event):
    side: str   # "BUY" ou "SELL"
    confidence: float
    price: float = None


# ✅ Trade validé par le Risk Manager
@dataclass
class TradeApproved(Event):
    side: str
    size: float
    price: float
    tp: float
    sl: float

# Trade Close par le Trader
@dataclass
class TradeClose(Event):
    side: str
    size: float
    price: float
    tp: float
    sl: float

# ❌ Trade rejeté
@dataclass
class TradeRejected(Event):
    reason: str
