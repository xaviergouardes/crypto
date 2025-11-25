import abc
import asyncio
import pandas as pd
from typing import Dict

from trading_bot.system_trading.system import System

class Engine(abc.ABC):
    """
    Classe abstraite pour un moteur d'exécution.
    Peut être un moteur backtest ou temps réel.
    """

    def __init__(self, system: System, params: Dict):
        """
        Args:
            system (System): Instance du système de trading.
            params (dict): Paramètres du bot.
        """
        self.system = system
        self.params = params

    @abc.abstractmethod
    async def run(self):
        """
        Méthode principale qui démarre l'exécution du moteur.
        Doit être implémentée par les classes concrètes.
        """
        pass

    @abc.abstractmethod
    async def stop(self):
        """
        Méthode pour arrêter proprement l'exécution.
        """
        pass
