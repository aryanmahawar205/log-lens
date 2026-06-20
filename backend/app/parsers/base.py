from abc import ABC, abstractmethod
from typing import Iterator, Optional
from app.models.schema import NormalizedLogEntry

class BaseParser(ABC):
    """
    Abstract base class for all log parsers.
    Parsers are responsible for reading log lines and converting them
    into NormalizedLogEntry objects.
    """

    @abstractmethod
    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        """
        Parse a single log line into a NormalizedLogEntry.
        Should return None if the line is invalid or unparseable.
        """
        pass

    def parse_file(self, file_path: str) -> Iterator[NormalizedLogEntry]:
        """
        Read a file line by line and yield parsed log entries.
        """
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                entry = self.parse_line(line.strip())
                if entry:
                    yield entry
