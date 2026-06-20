import pytest
from app.parsers.apache import ApacheAccessParser
from app.parsers.apache_error import ApacheErrorParser
from datetime import datetime, timezone, timedelta

def test_apache_access_parser():
    parser = ApacheAccessParser()
    line = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif?id=1 HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.ip == "127.0.0.1"
    assert entry.method == "GET"
    assert entry.url == "/apache_pb.gif"
    assert entry.query_string == "id=1"
    assert entry.status_code == 200
    assert entry.bytes_sent == 2326
    assert entry.referrer == "http://www.example.com/start.html"
    assert entry.user_agent == "Mozilla/4.08 [en] (Win98; I ;Nav)"
    assert entry.protocol == "HTTP/1.0"

    tz = timezone(timedelta(hours=-7))
    assert entry.timestamp == datetime(2000, 10, 10, 13, 55, 36, tzinfo=tz)

def test_apache_access_parser_invalid():
    parser = ApacheAccessParser()
    entry = parser.parse_line("invalid line")
    assert entry is None

def test_apache_error_parser():
    parser = ApacheErrorParser()
    line = '[Sat Oct 10 13:55:36 2000] [error] [client 127.0.0.1] File does not exist: /usr/local/apache/htdocs/favicon.ico'

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.ip == "127.0.0.1"
    assert entry.status_code == 500
    assert entry.timestamp == datetime(2000, 10, 10, 13, 55, 36)
