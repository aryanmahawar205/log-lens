from typing import Optional, List
from app.models.schema import NormalizedLogEntry
from app.parsers.base import BaseParser
from abc import abstractmethod

class BaseAIParser(BaseParser):
    """
    Interface for AI-assisted parsing.
    Implementing classes should provide mechanisms to ingest sample lines,
    query an LLM or AI model to generate regex patterns/mappings,
    and output NormalizedLogEntry.
    This component is disabled by default and ensures the system remains offline-safe.
    """

    def __init__(self, sample_lines: List[str] = None):
        super().__init__()
        self.sample_lines = sample_lines or []
        self._pattern = None
        if self.sample_lines:
            self._train(self.sample_lines)

    @abstractmethod
    def _train(self, sample_lines: List[str]):
        """
        Subclasses should implement logic to ask an AI model to detect
        a parsing regex or JSON mapping from the sample_lines.
        """
        pass

    @abstractmethod
    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        """
        Parse a single log line using the AI-generated pattern.
        """
        pass
