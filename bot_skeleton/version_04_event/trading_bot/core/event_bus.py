# trading_bot/core/event_bus.py
import asyncio
from typing import Callable, Dict, List, Type

class Event:
    """Classe de base pour tous les événements."""
    pass

class EventBus:
    """Bus d'événements asynchrone (pub/sub)."""
    
    def __init__(self):
        self._subscribers: Dict[Type[Event], List[Callable]] = {}

    def subscribe(self, event_type: Type[Event], callback: Callable):
        """S'abonner à un type d'événement."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def publish(self, event: Event):
        """Publie un événement et appelle tous les abonnés."""
        event_type = type(event)
        if event_type in self._subscribers:
             await asyncio.gather(*[cb(event) for cb in self._subscribers[event_type]])

    def unsubscribe(self, event_type, callback):
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def unsubscribe_all(self):
        """Désinscrit tous les abonnés sans supprimer les types d'événements."""
        for event_type in self._subscribers:
            self._subscribers[event_type].clear()