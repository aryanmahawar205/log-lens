import re
from datetime import datetime
from typing import Optional
from app.models.schema import NormalizedLogEntry
from app.parsers.base import BaseParser
from app.parsers.registry import ParserRegistry

@ParserRegistry.register("iis_w3c")
class IISW3CParser(BaseParser):
    """
    Parser for IIS W3C Extended Log Format.
    #Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) cs(Referer) sc-status sc-substatus sc-win32-status time-taken
    2002-05-02 17:42:15 172.22.255.255 GET /images/picture.jpg - 80 - 172.20.255.255 Mozilla/4.0+(compatible;MSIE+5.5;+Windows+2000+Server) - 200 0 0 10
    """

    LOG_PATTERN = re.compile(
        r'(?P<date>\d{4}-\d{2}-\d{2})\s+'           # date
        r'(?P<time>\d{2}:\d{2}:\d{2})\s+'           # time
        r'(?P<s_ip>\S+)\s+'                         # s-ip
        r'(?P<method>\S+)\s+'                       # cs-method
        r'(?P<url>\S+)\s+'                          # cs-uri-stem
        r'(?P<query>\S+)\s+'                        # cs-uri-query
        r'(?P<s_port>\S+)\s+'                       # s-port
        r'(?P<cs_username>\S+)\s+'                  # cs-username
        r'(?P<c_ip>\S+)\s+'                         # c-ip
        r'(?P<user_agent>\S+)\s+'                   # cs(User-Agent)
        r'(?P<referer>\S+)\s+'                      # cs(Referer)
        r'(?P<status>\d+)\s+'                       # sc-status
        r'(?P<substatus>\d+)\s+'                    # sc-substatus
        r'(?P<win32_status>\d+)\s+'                 # sc-win32-status
        r'(?P<time_taken>\d+)'                      # time-taken
    )

    def parse_line(self, line: str) -> Optional[NormalizedLogEntry]:
        if line.startswith('#'):
            return None

        match = self.LOG_PATTERN.search(line)
        if not match:
            return None

        data = match.groupdict()

        try:
            timestamp_str = f"{data['date']} {data['time']}"
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

        query_string = data['query'] if data['query'] != '-' else None

        user_agent = data['user_agent'].replace('+', ' ') if data['user_agent'] != '-' else None
        referrer = data['referer'] if data['referer'] != '-' else None

        # IIS time-taken is usually in milliseconds
        time_taken = int(data['time_taken']) if data['time_taken'] != '-' else None

        return NormalizedLogEntry(
            timestamp=timestamp,
            ip=data['c_ip'],
            method=data['method'],
            url=data['url'],
            query_string=query_string,
            status_code=int(data['status']),
            bytes_sent=0, # IIS default doesn't always have sc-bytes unless configured
            response_time_ms=time_taken,
            referrer=referrer,
            user_agent=user_agent
        )
