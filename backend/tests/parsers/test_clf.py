import pytest
from app.parsers.clf import CLFParser
from datetime import datetime, timezone, timedelta

def test_clf_parser():
    parser = CLFParser()
    line = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.ip == "127.0.0.1"
    assert entry.method == "GET"
    assert entry.url == "/apache_pb.gif"
    assert entry.status_code == 200
    assert entry.bytes_sent == 2326
    assert entry.protocol == "HTTP/1.0"
