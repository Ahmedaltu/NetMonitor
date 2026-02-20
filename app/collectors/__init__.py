# Collector plugin loader
import importlib
import pkgutil
from .base import BaseCollector

def load_plugins():
    plugins = []
    package = __name__
    for _, modname, ispkg in pkgutil.iter_modules(__path__):
        if modname in ("base", "__init__"): continue
        module = importlib.import_module(f"{package}.{modname}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, BaseCollector) and obj is not BaseCollector:
                plugins.append(obj())
    return plugins
