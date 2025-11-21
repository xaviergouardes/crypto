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

    def compute_warmup_count(self) -> int:
        # Priorité au warmup_count fourni dans les params
        warmup_count = self.params.get("warmup_count", None)

        if warmup_count is None:
            # Warmup = max de tous les paramètres numériques (sauf initial_capital)
            excluded = {"initial_capital", "swing_side", "tp_pct", "sl_pct"}  # si tu veux en exclure d’autres
            numeric_values = [v for k, v in self.params.items() if k not in excluded and isinstance(v,(int,float))]
            if numeric_values:
                warmup_count =  max(numeric_values)
            else:
                warmup_count =  0
            self.params["warmup_count"] = warmup_count
        
        return self.params

    @abc.abstractmethod
    def start_piepline(self):
        """
        Méthode principale qui démarre l'exécution du mopipeline de traitement du système de trading
        Doit être implémentée par les classes concrètes.
        """
        pass

