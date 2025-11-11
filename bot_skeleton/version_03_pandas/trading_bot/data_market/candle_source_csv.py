import asyncio
import pandas as pd
import pytz
from .candle_source import CandleSource

# Fuseau horaire Paris
PARIS_TZ = pytz.timezone("Europe/Paris")

class CandleSourceCsv(CandleSource):
    """
    Source de données basée sur un fichier CSV.
    Fournit les bougies soit en bloc (get_initial_data),
    soit sous forme de flux simulé (stream_candles).
    """

    def __init__(self, path: str):
        self.path = path

    def get_initial_data(self) -> pd.DataFrame:
        """
        Charge le fichier CSV et renvoie un DataFrame propre.
        Le CSV doit contenir au minimum : timestamp, open, high, low, close, volume
        """
        df = pd.read_csv(self.path)

        # Nettoyage de base
        df.columns = [c.strip().lower() for c in df.columns]

        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Colonnes manquantes dans le CSV : {missing}")

        # Conversion des timestamps en datetime UTC
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        df = df.dropna(subset=["timestamp"]).reset_index(drop=True)

        # Ajout de la colonne timestamp_paris
        df["timestamp_paris"] = df["timestamp"].dt.tz_convert(PARIS_TZ)

        return df

    async def stream_candles(self, on_new_candle):
        raise RuntimeError("stream_candles ne doit pas être utilisé en mode backtest !")
