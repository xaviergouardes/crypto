# trading_bot/core/events.py
from dataclasses import dataclass
from typing import List, Tuple
from .event_bus import Event
from datetime import datetime, timedelta

# 📈 Structure de type prix
@dataclass
class Price(Event):
    symbol: str
    price: float
    volume: float
    timestamp: datetime

# 📈 Événement : nouveau prix reçu
@dataclass
class PriceUpdated(Event):
    price: Price

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
    timestamp: datetime
    values: dict  # ex: {"sma": 123.45, "momentum": 0.67}

# 📊 Signal de stratégie
@dataclass
class TradeSignalGenerated(Event):
    side: str   # "BUY" ou "SELL"
    confidence: float
    price: Price = None


# ✅ Trade validé par le Risk Manager
@dataclass
class TradeApproved(Event):
    side: str
    size: float
    price: Price
    tp: float
    sl: float

# Trade Close par le Trader
@dataclass
class TradeClose(Event):
    side: str
    size: float
    price: Price
    tp: float
    sl: float
    target: str # TP / SL
    open_timestamp: datetime
    close_timestamp: datetime

# ❌ Trade rejeté
@dataclass
class TradeRejected(Event):
    reason: str

# Une structure de type Chandelier
@dataclass
class Candle(Event):
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    start_time: datetime
    end_time: datetime

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

# 
@dataclass
class StopBot(Event):
    timestamp: datetime