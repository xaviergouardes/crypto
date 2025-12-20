import re

class Timeframe:
    """
    Utilitaire de conversion timeframe <-> secondes
    Exemples :
        "5m"  -> 300
        "1h"  -> 3600
        "1d"  -> 86400
    """

    _MULTIPLIERS = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }

    _PATTERN = re.compile(r"^(\d+)([smhd])$")

    @classmethod
    def to_seconds(cls, timeframe: str) -> int:
        """
        Convertit '5m' → 300
        """
        match = cls._PATTERN.match(timeframe)
        if not match:
            raise ValueError(f"Timeframe invalide : {timeframe}")

        value, unit = match.groups()
        return int(value) * cls._MULTIPLIERS[unit]

    @classmethod
    def from_seconds(cls, seconds: int) -> str:
        """
        Convertit 300 → '5m'
        Choisit l’unité la plus lisible
        """
        if seconds <= 0:
            raise ValueError("Les secondes doivent être > 0")

        for unit, multiplier in reversed(cls._MULTIPLIERS.items()):
            if seconds % multiplier == 0:
                return f"{seconds // multiplier}{unit}"

        return f"{seconds}s"
