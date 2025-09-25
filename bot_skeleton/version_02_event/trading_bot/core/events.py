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
    support: float
    resistance: float

# 📉 Indicateur technique généré
@dataclass
class IndicatorSignalGenerated(Event):
    signal: str
    value: float

# 📊 Signal de stratégie
@dataclass
class TradeSignalGenerated(Event):
    side: str   # "BUY" ou "SELL"
    confidence: float

# ✅ Trade validé par le Risk Manager
@dataclass
class TradeApproved(Event):
    side: str
    size: float
    price: float

# ❌ Trade rejeté
@dataclass
class TradeRejected(Event):
    reason: str
