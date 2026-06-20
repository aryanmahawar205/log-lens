import pytest
from datetime import datetime, timezone, timedelta
from app.parsers.apache import ApacheAccessParser
from app.models.schema import NormalizedLogEntry

def test_apache_access_parser_valid_line():
    parser = ApacheAccessParser()
    line = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif?test=1 HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.ip == "127.0.0.1"
    assert entry.method == "GET"
    assert entry.url == "/apache_pb.gif"
    assert entry.query_string == "test=1"
    assert entry.status_code == 200
    assert entry.bytes_sent == 2326
    assert entry.referrer == "http://www.example.com/start.html"
    assert entry.user_agent == "Mozilla/4.08 [en] (Win98; I ;Nav)"
    assert entry.protocol == "HTTP/1.0"

    # Check timestamp logic
    expected_time = datetime(2000, 10, 10, 13, 55, 36, tzinfo=timezone(timedelta(hours=-7)))
    assert entry.timestamp == expected_time

def test_apache_access_parser_invalid_line():
    parser = ApacheAccessParser()
    line = "this is not a valid apache log line"

    entry = parser.parse_line(line)
    assert entry is None

def test_apache_access_parser_dash_values():
    parser = ApacheAccessParser()
    # Missing bytes (-), referrer (-), user-agent (-)
    line = '192.168.1.1 - - [10/Oct/2000:13:55:36 -0700] "GET / HTTP/1.1" 404 - "-" "-"'

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.status_code == 404
    assert entry.bytes_sent == 0
    assert entry.referrer is None
    assert entry.user_agent is None
