import pytest
from app.parsers.nginx_access import NginxAccessParser
from app.parsers.nginx_error import NginxErrorParser
from datetime import datetime, timezone, timedelta

def test_nginx_access_parser():
    parser = NginxAccessParser()
    line = '192.168.1.10 - - [15/Nov/2023:14:20:00 +0000] "POST /api/login HTTP/1.1" 201 500 "-" "PostmanRuntime/7.28.4"'

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.ip == "192.168.1.10"
    assert entry.method == "POST"
    assert entry.url == "/api/login"
    assert entry.status_code == 201
    assert entry.bytes_sent == 500
    assert entry.referrer is None
    assert entry.user_agent == "PostmanRuntime/7.28.4"
    assert entry.protocol == "HTTP/1.1"

def test_nginx_error_parser():
    parser = NginxErrorParser()
    line = '2023/10/24 15:34:20 [error] 11#11: *1 open() "/usr/share/nginx/html/favicon.ico" failed (2: No such file or directory), client: 192.168.1.1, server: localhost, request: "GET /favicon.ico HTTP/1.1", host: "localhost"'

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.ip == "192.168.1.1"
    assert entry.method == "GET"
    assert entry.url == "/favicon.ico"
    assert entry.status_code == 500
    assert entry.host == "localhost"
    assert entry.timestamp == datetime(2023, 10, 24, 15, 34, 20)
