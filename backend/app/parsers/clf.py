import re
import urllib.parse
from datetime import datetime
from typing import Optional
from app.models.schema import NormalizedLogEntry
from app.parsers.base import BaseParser
from app.parsers.registry import ParserRegistry

@ParserRegistry.register("clf")
class CLFParser(BaseParser):
    """
    Parser for Common Log Format (CLF).
    Format: %h %l %u %t "%r" %>s %b
    Example: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
    """

    LOG_PATTERN = re.compile(
        r'(?P<ip>\S+)\s+'                 # IP address
        r'\S+\s+'                         # Remote logname (ignored)
        r'\S+\s+'                         # Remote user (ignored)
        r'\[(?P<timestamp>[^\]]+)\]\s+'   # Time
        r'"(?P<method>\S+)\s+'            # Method
        r'(?P<url>.+)\s+'                  # URL (greedy to handle spaces in payload)
        r'(?P<protocol>HTTP/\d\.\d)"\s+'  # Protocol (specific to standard HTTP)
        r'(?P<status_code>\d{3})\s+'      # Status code
        r'(?P<bytes_sent>\S+)'            # Bytes
    )

    # Fallback pattern for malformed/aggressive payloads
    FALLBACK_PATTERN = re.compile(
        r'(?P<ip>\S+)\s+'
        r'\S+\s+\S+\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<request>[^"]+)"\s+'
        r'(?P<status_code>\d{3})\s+'
        r'(?P<bytes_sent>\S+)'
    )

    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        match = self.LOG_PATTERN.search(line)
        if match:
            data = match.groupdict()
            method = data['method']
            full_url = data['url']
            protocol = data['protocol']
        else:
            # Try fallback for malformed requests
            match = self.FALLBACK_PATTERN.search(line)
            if not match:
                return None
            data = match.groupdict()
            request_parts = data['request'].split(' ')
            method = request_parts[0] if len(request_parts) > 0 else "UNKNOWN"

            if len(request_parts) > 1 and "HTTP" in request_parts[-1]:
                protocol = request_parts[-1]
                url_end_idx = -1
            else:
                protocol = "UNKNOWN"
                url_end_idx = None # Take all remaining as URL if no HTTP protocol found

            if url_end_idx is not None:
                if len(request_parts) > 2:
                    full_url = " ".join(request_parts[1:url_end_idx])
                elif len(request_parts) == 2:
                    full_url = request_parts[1] if "HTTP" not in request_parts[1] else "/"
                else:
                    full_url = "/"
            else:
                if len(request_parts) > 1:
                    full_url = " ".join(request_parts[1:])
                else:
                    full_url = "/"

        try:
            timestamp = datetime.strptime(data['timestamp'], '%d/%b/%Y:%H:%M:%S %z')
        except ValueError:
            return None

        bytes_sent = data['bytes_sent']
        bytes_sent = 0 if bytes_sent == '-' else int(bytes_sent)

        url_parts = full_url.split('?', 1)
        url = urllib.parse.unquote(url_parts[0])
        query_string = urllib.parse.unquote(url_parts[1]) if len(url_parts) > 1 else None

        return NormalizedLogEntry(
            timestamp=timestamp,
            ip=data['ip'],
            method=method,
            url=url,
            query_string=query_string,
            status_code=int(data['status_code']),
            bytes_sent=bytes_sent,
            protocol=protocol
        )
