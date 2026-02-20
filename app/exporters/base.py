# app/exporters/base.py

from abc import ABC, abstractmethod

class BaseExporter(ABC):

    @abstractmethod
    def export(self, metrics: dict):
        """
        Export metrics dictionary to external system.
        """
        pass
