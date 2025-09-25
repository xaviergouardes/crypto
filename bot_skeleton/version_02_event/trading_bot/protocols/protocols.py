from typing import Protocol

# Responsabilité : récupérer les prix en temps réel depuis Binance.
# Rôle : alimenter l’état partagé (SharedState) avec la valeur actuelle du prix.
# Sortie : state["price"].
class MarketDataProtocol(Protocol):
    async def run(self) -> None: ...

# Responsabilité : récupérer le carnet d’ordres (bids / asks) depuis Binance.
# Rôle : alimenter l’état partagé avec les dernières données du carnet d’ordres.
# Sortie : state["order_book"] (ex. {"bids": [...], "asks": [...]}).
class OrderBookDataProtocol(Protocol):
    async def run(self) -> None: ...

# Responsabilité : analyser le carnet d’ordres pour détecter les zones clés du marché, comme :
# les supports et résistances basés sur les volumes dans le carnet
# les liquidités importantes (grands ordres qui peuvent influencer le prix)
# Rôle : traiter state["order_book"] et calculer des niveaux utiles pour la stratégie.
# Sortie :
# state["support"]
# state["resistance"]
# éventuellement d’autres informations comme state["liquidity_zones"]
class OrderBookAnalyzerProtocol(Protocol):
    async def run(self) -> None: ...

# Responsabilité : calculer des indicateurs basés sur le prix (ex. moyenne, oscillateur…).
# Rôle : mettre à disposition des valeurs calculées pour la stratégie.
# Sortie : state["indicator"].
class IndicatorEngineProtocol(Protocol):
    async def run(self) -> None: ...

# Responsabilité : produire un signal de trading (BUY, SELL, HOLD).
# Rôle : analyser l’indicateur et le carnet d’ordres pour détecter support/résistance et décider de l’action.
# Sortie :
# state["support"]
# state["resistance"]
# state["signal"]
class StrategyProtocol(Protocol):
    async def run(self) -> None: ...

# Responsabilité : vérifier la conformité des signaux avec les règles de gestion du risque.
# Rôle : filtrer ou ajuster les signaux avant qu’ils ne soient envoyés au trader.
# Sortie : peut modifier state["signal"] ou produire des logs.
class RiskManagerProtocol(Protocol):
    async def run(self) -> None: ...

# Responsabilité : exécuter le trade.
# Rôle : utiliser le signal validé pour acheter ou vendre (ici en simulation).
# Sortie : log ou exécution de trade réel/fictif.
class TraderProtocol(Protocol):
    async def run(self) -> None: ...