from abc import ABC, abstractmethod

class Startable(ABC):
    """
    Interface simple pour tout composant qui peut être démarré/arrêté.
    Gère automatiquement l'état interne _running.
    """

    def __init__(self):
        self._running = False

    async def start(self):
        """Démarre le composant."""
        self._running = True
        return await self._on_start()

    def stop(self):
        """Arrête le composant."""
        self._on_stop()
        self._running = False

    @abstractmethod
    async def _on_start(self):
        """Méthode à implémenter : logique lors du démarrage."""
        pass

    @abstractmethod
    def _on_stop(self):
        """Méthode à implémenter : logique lors de l'arrêt."""
        pass

    def is_running(self):
        return self._running