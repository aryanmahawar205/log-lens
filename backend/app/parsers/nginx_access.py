import re
from datetime import datetime
from typing import Optional
from app.models.schema import NormalizedLogEntry
from app.parsers.base import BaseParser
from app.parsers.registry import ParserRegistry

@ParserRegistry.register("nginx_access")
class NginxAccessParser(BaseParser):
    """
    Parser for Nginx Combined Access Logs.
    Format typically: $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
    """

    LOG_PATTERN = re.compile(
        r'(?P<ip>\S+)\s+'                 # IP address
        r'\S+\s+'                         # Remote user (ignored)
        r'\S+\s+'                         # Remote user (ignored)
        r'\[(?P<timestamp>[^\]]+)\]\s+'   # Time
        r'"(?P<method>\S+)\s+'            # Method
        r'(?P<url>.+)\s+'                 # URL (greedy)
        r'(?P<protocol>HTTP/\d\.\d)"\s+'  # Protocol
        r'(?P<status_code>\d{3})\s+'      # Status code
        r'(?P<bytes_sent>\S+)\s+'         # Bytes
        r'"(?P<referrer>[^"]*)"\s+'       # Referer
        r'"(?P<user_agent>[^"]*)"'        # User-Agent
        r'(?:\s+(?P<latency>[0-9.]+))?'   # Optional Latency ($request_time in seconds)
    )

    # Fallback for malformed requests
    FALLBACK_PATTERN = re.compile(
        r'(?P<ip>\S+)\s+\S+\s+\S+\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<request>[^"]+)"\s+'
        r'(?P<status_code>\d{3})\s+'
        r'(?P<bytes_sent>\S+)\s+'
        r'"(?P<referrer>[^"]*)"\s+'
        r'"(?P<user_agent>[^"]*)"'
    )

    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        match = self.LOG_PATTERN.search(line)
        if match:
            data = match.groupdict()
            method = data['method']
            full_url = data['url']
            protocol = data['protocol']
        else:
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
                url_end_idx = None

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

        # Parse timestamp: 10/Oct/2000:13:55:36 -0700
        try:
            timestamp = datetime.strptime(data['timestamp'], '%d/%b/%Y:%H:%M:%S %z')
        except ValueError:
            return None

        bytes_sent = data['bytes_sent']
        bytes_sent = 0 if bytes_sent == '-' else int(bytes_sent)

        url_parts = full_url.split('?', 1)
        url = url_parts[0]
        query_string = url_parts[1] if len(url_parts) > 1 else None

        # Convert seconds to milliseconds if present
        response_time_ms = None
        if data.get('latency'):
            response_time_ms = float(data['latency']) * 1000.0

        return NormalizedLogEntry(
            timestamp=timestamp,
            ip=data['ip'],
            method=method,
            url=url,
            query_string=query_string,
            status_code=int(data['status_code']),
            bytes_sent=bytes_sent,
            referrer=data['referrer'] if data['referrer'] != '-' else None,
            user_agent=data['user_agent'] if data['user_agent'] != '-' else None,
            protocol=protocol,
            response_time_ms=response_time_ms
        )
