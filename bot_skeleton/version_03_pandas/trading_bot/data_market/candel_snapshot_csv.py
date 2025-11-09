import pandas as pd
import pytz

class CandelSnapshotCsv:
    def __init__(self, path_file: str):
        self.path_file = path_file
        self.df = None

    def load(self):
        # Lecture du fichier CSV avec parsing automatique de la colonne timestamp
        df = pd.read_csv(self.path_file, parse_dates=['timestamp'])
        df.set_index('timestamp', inplace=True)

        # Conversion de l'index vers le fuseau horaire de Paris
        if df.index.tz is None:
            # Si le timestamp n’a pas de fuseau, on suppose qu’il est en UTC
            df.index = df.index.tz_localize('UTC')

        # Ajout d'une colonne timestamp_paris
        df['timestamp_paris'] = df.index.tz_convert('Europe/Paris')

        self.df = df
        return self.df
