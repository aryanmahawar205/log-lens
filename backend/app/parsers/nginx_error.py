import re
from datetime import datetime
from typing import Optional
from app.models.schema import NormalizedLogEntry
from app.parsers.base import BaseParser
from app.parsers.registry import ParserRegistry

@ParserRegistry.register("nginx_error")
class NginxErrorParser(BaseParser):
    """
    Parser for Nginx Error Logs.
    Format typically: 2023/10/24 15:34:20 [error] 11#11: *1 open() "/usr/share/nginx/html/favicon.ico" failed (2: No such file or directory), client: 192.168.1.1, server: localhost, request: "GET /favicon.ico HTTP/1.1", host: "localhost"
    """

    LOG_PATTERN = re.compile(
        r'(?P<timestamp>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\s+'
        r'\[(?P<level>\w+)\]\s+'
        r'(?P<pid_tid>\d+#\d+):\s+'
        r'(?P<cid>\*\d+)?\s*'
        r'(?P<message>.*)'
    )

    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        match = self.LOG_PATTERN.search(line)
        if not match:
            return None

        data = match.groupdict()

        try:
            # Timestamp format like: 2023/10/24 15:34:20
            timestamp = datetime.strptime(data['timestamp'], '%Y/%m/%d %H:%M:%S')
        except ValueError:
            return None

        message = data.get('message', '')

        # Extract optional fields from the message tail
        ip_match = re.search(r'client:\s*([^,]+)', message)
        ip = ip_match.group(1) if ip_match else "-"

        server_match = re.search(r'server:\s*([^,]+)', message)
        server = server_match.group(1) if server_match else None

        req_match = re.search(r'request:\s*"(\w+)\s+([^\s]+)\s+([^"]+)"', message)
        if req_match:
            method, url, protocol = req_match.groups()
        else:
            method, url, protocol = "-", "-", None

        host_match = re.search(r'host:\s*"([^"]+)"', message)
        host = host_match.group(1) if host_match else None

        # default to 500 for generic errors or map from level
        status_code = 500

        query_string = None
        if url != "-":
            url_parts = url.split('?', 1)
            url = url_parts[0]
            if len(url_parts) > 1:
                query_string = url_parts[1]

        return NormalizedLogEntry(
            timestamp=timestamp,
            ip=ip,
            method=method,
            url=url,
            query_string=query_string,
            status_code=status_code,
            bytes_sent=0,
            protocol=protocol,
            host=host
        )
