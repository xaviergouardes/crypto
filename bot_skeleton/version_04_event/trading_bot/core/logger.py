import logging

class Logger:
    """
    Wrapper simple autour de logging pour masquer son utilisation.
    Si tu veux changer d’implémentation (ex: envoyer vers Elastic, fichiers, stdout, etc.),
    tu n’as qu’à modifier cette classe.
    """
    _loggers = {}

    @classmethod
    def get(cls, name: str = "App"):
        """Retourne un logger déjà créé ou en crée un nouveau."""
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name)
        return cls._loggers[name]

    @classmethod
    def _create_logger(cls, name):
        logger = logging.getLogger(name)

        if not logger.handlers:  # éviter les doublons en mode multi-import
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    # --- Méthodes simplifiées ---
    @classmethod
    def info(cls, msg: str, name="App"):
        cls.get(name).info(msg)

    @classmethod
    def warning(cls, msg: str, name="App"):
        cls.get(name).warning(msg)

    @classmethod
    def error(cls, msg: str, name="App"):
        cls.get(name).error(msg)

    @classmethod
    def debug(cls, msg: str, name="App"):
        cls.get(name).debug(msg)
