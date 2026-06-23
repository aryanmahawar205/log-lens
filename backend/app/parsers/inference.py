import re
from datetime import datetime
from typing import Optional
from app.models.schema import NormalizedLogEntry
from app.parsers.base import BaseParser
import json
from app.parsers.registry import ParserRegistry

@ParserRegistry.register("UNKNOWN_FORMAT")
class InferenceParser(BaseParser):
    """
    Fallback parser for UNKNOWN_FORMAT. Uses heuristics and regex to extract common fields.
    """

    IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    HTTP_METHOD_REGEX = re.compile(r'\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b')
    URL_REGEX = re.compile(r'\s(/[^\s?]+)(\?[^\s]+)?\s')
    STATUS_CODE_REGEX = re.compile(r'\s([1-5][0-9]{2})\s')
    BYTES_REGEX = re.compile(r'\s([1-5][0-9]{2})\s+([0-9]+|-)\s')
    LATENCY_REGEX = re.compile(r'\s([0-9]+(?:\.[0-9]+)?)(?:ms|µs|s)?\s*$')

    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        if not line:
            return None

        # Base default extraction
        ip = "0.0.0.0"
        method = "UNKNOWN"
        url = "/"
        status_code = 200
        bytes_sent = 0
        timestamp = datetime.now()
        user_agent = "Unknown"
        response_time_ms = None

        # Try extract IP
        ip_match = self.IP_REGEX.search(line)
        if ip_match:
            ip = ip_match.group(0)

        # Try extract method
        method_match = self.HTTP_METHOD_REGEX.search(line)
        if method_match:
            method = method_match.group(1)

        # Try extract URL
        url_match = self.URL_REGEX.search(line)
        query_string = None
        if url_match:
            url = url_match.group(1)
            query_string = url_match.group(2)
            if query_string:
                query_string = query_string.lstrip('?')

        # Try extract status code and bytes
        bytes_match = self.BYTES_REGEX.search(line)
        if bytes_match:
            status_code = int(bytes_match.group(1))
            b = bytes_match.group(2)
            if b.isdigit():
                bytes_sent = int(b)
        else:
            status_match = self.STATUS_CODE_REGEX.search(line)
            if status_match:
                status_code = int(status_match.group(1))

        # Try extract latency
        latency_match = self.LATENCY_REGEX.search(line)
        if latency_match:
            try:
                val = float(latency_match.group(1))
                unit_match = re.search(r'(ms|µs|s)$', line.strip())
                if unit_match:
                    unit = unit_match.group(1)
                    if unit == 's':
                        response_time_ms = val * 1000
                    elif unit == 'µs':
                        response_time_ms = val / 1000
                    else:
                        response_time_ms = val
                else:
                    response_time_ms = val # Assume ms
            except Exception:
                pass

        # Try extract user agent (loosely, anything in quotes at the end)
        ua_matches = re.findall(r'"([^"]*)"', line)
        if ua_matches:
            # Often UA is the last or second to last quoted string
            potential_ua = ua_matches[-1]
            if "Mozilla" in potential_ua or "Opera" in potential_ua or "compatible" in potential_ua:
                user_agent = potential_ua
            elif len(ua_matches) > 1:
                potential_ua = ua_matches[-2]
                if "Mozilla" in potential_ua or "Opera" in potential_ua:
                    user_agent = potential_ua

        # Try to find a date loosely, but if not we just use now
        # Very naive bracket date lookup
        date_match = re.search(r'\[(.*?)\]', line)
        if date_match:
            # try naive parsing
            try:
                # e.g. 10/Oct/2023:13:55:36 +0000
                ds = date_match.group(1)
                timestamp = datetime.strptime(ds.split()[0], "%d/%b/%Y:%H:%M:%S")
            except Exception:
                pass

        # Naive JSON parsing if it's curly braces
        if line.strip().startswith('{') and line.strip().endswith('}'):
            try:
                data = json.loads(line)
                if 'ip' in data: ip = data['ip']
                if 'client_ip' in data: ip = data['client_ip']
                if 'method' in data: method = data['method']
                if 'url' in data: url = data['url']
                if 'path' in data: url = data['path']
                if 'status' in data: status_code = int(data['status'])
                if 'status_code' in data: status_code = int(data['status_code'])
                if 'bytes' in data: bytes_sent = int(data['bytes'])
                if 'user_agent' in data: user_agent = data['user_agent']
                if 'timestamp' in data:
                    try:
                        # Attempt standard ISO 8601 parsing
                        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    except Exception:
                        pass
            except Exception:
                pass

        return NormalizedLogEntry(
            timestamp=timestamp,
            ip=ip,
            method=method,
            url=url,
            query_string=query_string,
            status_code=status_code,
            bytes_sent=bytes_sent,
            user_agent=user_agent,
            response_time_ms=response_time_ms
        )
