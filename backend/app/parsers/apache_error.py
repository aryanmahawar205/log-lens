import re
from datetime import datetime
from typing import Optional
from app.models.schema import NormalizedLogEntry
from app.parsers.base import BaseParser
from app.parsers.registry import ParserRegistry

@ParserRegistry.register("apache_error")
class ApacheErrorParser(BaseParser):
    """
    Parser for Apache Error Logs.
    Format typically: [Sat Oct 10 13:55:36 2000] [error] [client 127.0.0.1] File does not exist: /usr/local/apache/htdocs/favicon.ico
    """

    LOG_PATTERN = re.compile(
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'\[(?P<level>\w+)\]\s+'
        r'\[client\s+(?P<ip>[^\]]+)\]\s+'
        r'(?P<message>.*)'
    )

    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        match = self.LOG_PATTERN.search(line)
        if not match:
            return None

        data = match.groupdict()

        try:
            # Timestamp format like: Sat Oct 10 13:55:36 2000
            # or Sat Oct 10 13:55:36.123456 2000 (we might need to handle microseconds, but lets start with standard)
            # Try to strip microsecond if present
            timestamp_str = data['timestamp']
            if '.' in timestamp_str:
                 parts = timestamp_str.split('.')
                 time_part = parts[0]
                 year_part = parts[1].split(' ')[1]
                 timestamp_str = f"{time_part} {year_part}"

            timestamp = datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %Y')
        except ValueError:
            return None

        # For error logs, we don't have all access fields
        return NormalizedLogEntry(
            timestamp=timestamp,
            ip=data['ip'],
            method="-",  # Method usually missing from simple error format unless extracted from message
            url="-",     # Extracted from message if we do more advanced parsing
            status_code=500, # default to 500 for generic errors or map from level
            bytes_sent=0
        )
