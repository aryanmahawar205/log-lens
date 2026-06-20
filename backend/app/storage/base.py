from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from app.models.schema import NormalizedLogEntry

class BaseStorage(ABC):
    """
    Abstract base class for the storage layer.
    """

    @abstractmethod
    def initialize(self):
        """Initialize the storage schema."""
        pass

    @abstractmethod
    def ingest_batch(self, entries: List[NormalizedLogEntry]):
        """Ingest a batch of NormalizedLogEntry objects."""
        pass

    @abstractmethod
    def execute_query(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return the results as a list of dictionaries."""
        pass
