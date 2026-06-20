import pytest
from app.parsers.iis import IISW3CParser
from datetime import datetime

def test_iis_parser():
    parser = IISW3CParser()
    line = '2002-05-02 17:42:15 172.22.255.255 GET /images/picture.jpg - 80 - 172.20.255.255 Mozilla/4.0+(compatible;MSIE+5.5;+Windows+2000+Server) - 200 0 0 10'

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.ip == "172.20.255.255"
    assert entry.method == "GET"
    assert entry.url == "/images/picture.jpg"
    assert entry.status_code == 200
    assert entry.user_agent == "Mozilla/4.0 (compatible;MSIE 5.5; Windows 2000 Server)"
    assert entry.response_time_ms == 10
    assert entry.timestamp == datetime(2002, 5, 2, 17, 42, 15)

def test_iis_parser_comment():
    parser = IISW3CParser()
    line = '#Software: Microsoft Internet Information Services 6.0'
    entry = parser.parse_line(line)
    assert entry is None
