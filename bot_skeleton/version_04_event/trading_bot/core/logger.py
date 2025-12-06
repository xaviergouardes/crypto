import logging

class Logger:
    _loggers = {}
    _default_level = logging.INFO
    _custom_levels = {}

    @classmethod
    def set_default_level(cls, level):
        cls._default_level = level
        # Forcer tous les loggers existants
        for logger in cls._loggers.values():
            logger.setLevel(level)
            logger.propagate = False
        # Forcer le root logger
        logging.getLogger().setLevel(level)

    @classmethod
    def set_level(cls, name: str, level):
        cls._custom_levels[name] = level
        if name in cls._loggers:
            cls._loggers[name].setLevel(level)
            cls._loggers[name].propagate = False

    @classmethod
    def get(cls, name="App"):
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name)
        return cls._wrap(cls._loggers[name])

    @classmethod
    def _create_logger(cls, name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        # Niveau spécifique ou global
        level = cls._custom_levels.get(name, cls._default_level)
        logger.setLevel(level)
        logger.propagate = False
        return logger

    @staticmethod
    def _wrap(logger):
        """Wrapper pour n’évaluer le message que si le niveau est actif"""
        class LoggerWrapper:
            def __init__(self, logger):
                self._logger = logger

            def debug(self, msg, *args, **kwargs):
                if self._logger.isEnabledFor(logging.DEBUG):
                    self._logger.debug(msg() if callable(msg) else msg, *args, **kwargs)

            def info(self, msg, *args, **kwargs):
                if self._logger.isEnabledFor(logging.INFO):
                    self._logger.info(msg() if callable(msg) else msg, *args, **kwargs)

            def warning(self, msg, *args, **kwargs):
                if self._logger.isEnabledFor(logging.WARNING):
                    self._logger.warning(msg() if callable(msg) else msg, *args, **kwargs)

            def error(self, msg, *args, **kwargs):
                if self._logger.isEnabledFor(logging.ERROR):
                    self._logger.error(msg() if callable(msg) else msg, *args, **kwargs)

            def critical(self, msg, *args, **kwargs):
                if self._logger.isEnabledFor(logging.CRITICAL):
                    self._logger.critical(msg() if callable(msg) else msg, *args, **kwargs)

        return LoggerWrapper(logger)

    @staticmethod
    def get_all_levels():
        result = {}
        for name, logger in Logger._loggers.items():
            result[name] = logging.getLevelName(logger.level)
        return result

    # Accès rapide via classe pour conserver compatibilité
    @classmethod
    def info(cls, msg, name="App"): cls.get(name).info(msg)
    @classmethod
    def warning(cls, msg, name="App"): cls.get(name).warning(msg)
    @classmethod
    def error(cls, msg, name="App"): cls.get(name).error(msg)
    @classmethod
    def debug(cls, msg, name="App"): cls.get(name).debug(msg)
