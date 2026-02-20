# app/collectors/base.py

from abc import ABC, abstractmethod

class BaseCollector(ABC):

    name: str

    @abstractmethod
    def collect(self) -> dict:
        """
        Collect metrics and return a dictionary.
        Example:
        {
            "latency": 23,
            "packet_loss": 0
        }
        """
        pass
