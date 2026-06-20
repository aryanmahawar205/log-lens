import re
from datetime import datetime
from typing import Optional
from app.models.schema import NormalizedLogEntry
from app.parsers.base import BaseParser

class ApacheAccessParser(BaseParser):
    """
    Parser for Apache Combined Access Logs.
    Format typically: %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"
    """

    # Example line:
    # 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"
    LOG_PATTERN = re.compile(
        r'(?P<ip>\S+)\s+'                 # IP address
        r'\S+\s+'                         # Remote logname (ignored)
        r'\S+\s+'                         # Remote user (ignored)
        r'\[(?P<timestamp>[^\]]+)\]\s+'   # Time
        r'"(?P<method>\S+)\s+'            # Method
        r'(?P<url>\S+)\s+'                # URL
        r'(?P<protocol>[^"]+)"\s+'        # Protocol
        r'(?P<status_code>\d{3})\s+'      # Status code
        r'(?P<bytes_sent>\S+)\s+'         # Bytes
        r'"(?P<referrer>[^"]*)"\s+'       # Referer
        r'"(?P<user_agent>[^"]*)"'        # User-Agent
    )

    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        match = self.LOG_PATTERN.search(line)
        if not match:
            return None

        data = match.groupdict()

        # Parse timestamp: 10/Oct/2000:13:55:36 -0700
        try:
            timestamp = datetime.strptime(data['timestamp'], '%d/%b/%Y:%H:%M:%S %z')
        except ValueError:
            return None

        bytes_sent = data['bytes_sent']
        bytes_sent = 0 if bytes_sent == '-' else int(bytes_sent)

        url_parts = data['url'].split('?', 1)
        url = url_parts[0]
        query_string = url_parts[1] if len(url_parts) > 1 else None

        return NormalizedLogEntry(
            timestamp=timestamp,
            ip=data['ip'],
            method=data['method'],
            url=url,
            query_string=query_string,
            status_code=int(data['status_code']),
            bytes_sent=bytes_sent,
            referrer=data['referrer'] if data['referrer'] != '-' else None,
            user_agent=data['user_agent'] if data['user_agent'] != '-' else None,
            protocol=data['protocol']
        )
