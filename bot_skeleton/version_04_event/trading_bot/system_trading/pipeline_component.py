import asyncio
from abc import ABC, abstractmethod
from typing import override
from trading_bot.core.startable import Startable  # ta classe Startable existante
import logging

class PipelineComponent(ABC):
    """
    Composant de pipeline Startable.
    Ces composant n'ont pas besion d'etre startable car ils sont ré-instancier à chaque redémarrage du bot
    Pour etre sur de s'executer avec les bons paramétres et aussi de s'initialiser avec le bon snapshot
    """

    def __init__(self):
        pass

    @abstractmethod
    async def execute(self):
        pass
