# Collector plugin loader
import importlib
import pkgutil
from .base import BaseCollector
from app.utils.logger import logger

def load_plugins(settings=None):
    plugins = []
    package = __name__
    for _, modname, ispkg in pkgutil.iter_modules(__path__):
        if modname in ("base", "__init__"):
            continue
        module = importlib.import_module(f"{package}.{modname}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, BaseCollector) and obj is not BaseCollector:
                try:
                    plugins.append(obj(settings=settings))
                except TypeError:
                    try:
                        plugins.append(obj())
                    except Exception as exc:
                        logger.error("Failed to load collector %s: %s", attr, exc)
                except Exception as exc:
                    logger.error("Failed to load collector %s: %s", attr, exc)
    return plugins
