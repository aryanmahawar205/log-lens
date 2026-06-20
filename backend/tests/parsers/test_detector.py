import pytest
from app.parsers.detector import FormatDetector
from app.parsers.registry import ParserRegistry
from app.parsers.apache import ApacheAccessParser
from app.parsers.apache_error import ApacheErrorParser
from app.parsers.nginx_access import NginxAccessParser
from app.parsers.nginx_error import NginxErrorParser
from app.parsers.iis import IISW3CParser
from app.parsers.clf import CLFParser

def test_detector_apache():
    lines = [
        '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
    ]
    parser_name, score = FormatDetector.detect_format(lines)
    # Could be apache_access or nginx_access since they share the same combined format,
    # but score should be 1.0.
    assert score == 1.0
    assert parser_name in ["apache_access", "nginx_access"]

def test_detector_iis():
    lines = [
        '2002-05-02 17:42:15 172.22.255.255 GET /images/picture.jpg - 80 - 172.20.255.255 Mozilla/4.0+(compatible;MSIE+5.5;+Windows+2000+Server) - 200 0 0 10'
    ]
    parser_name, score = FormatDetector.detect_format(lines)
    assert score == 1.0
    assert parser_name == "iis_w3c"

def test_detector_none():
    lines = [
        'this is random garbage'
    ]
    parser_name, score = FormatDetector.detect_format(lines)
    assert score == 0.0
    assert parser_name is None
