import pandas as pd

class LogLastTrade:

    header_printed = False

    def log(self, df: pd.DataFrame) -> pd.DataFrame:

        last_row = df.iloc[[-1]]  # DataFrame avec 1 ligne

        # ---- Affichage de l'entête une seule fois ----
        if not self.header_printed:
            header = ";".join(last_row.columns)
            print(header)
            self.header_printed = True

        # ---- Affichage de la dernière ligne en CSV ----
        csv_line = last_row.to_csv(sep=";", index=False, header=False).strip()
        print(csv_line)

        return df
