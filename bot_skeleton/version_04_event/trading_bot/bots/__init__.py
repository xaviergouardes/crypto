import importlib
import pkgutil

BOTS_CONFIG = {}

for module_info in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f"{__name__}.{module_info.name}")

    if hasattr(module, "BOT_NAME") and hasattr(module, "BOT_CONFIG"):
        BOTS_CONFIG[module.BOT_NAME] = module.BOT_CONFIG

__all__ = ["BOTS_CONFIG"]