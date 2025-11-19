import abc

from trading_bot.core.event_bus import EventBus

class System(abc.ABC):
    """
    Classe abstraite pour un system de trading = pipeline
    Peut être un moteur backtest ou temps réel.
    """
    def __init__(self, event_bus:EventBus, params:dict):
        self.event_bus =  event_bus
        self.params = params


    @abc.abstractmethod
    def start_piepline(self):
        """
        Méthode principale qui démarre l'exécution du mopipeline de traitement du système de trading
        Doit être implémentée par les classes concrètes.
        """
        pass

