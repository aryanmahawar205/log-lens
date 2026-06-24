
import pytest
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.parsers.clf import CLFParser
from app.storage.duckdb_storage import DuckDBStorage
from app.security.analyzer import SecurityAnalyzer

@pytest.fixture
def storage():
    return DuckDBStorage(":memory:")

@pytest.fixture
def analyzer(storage):
    return SecurityAnalyzer(storage)

def test_sql_injection_detection(storage, analyzer):
    log_line = '192.168.1.10 - - [22/Jun/2026:12:00:00 +0000] "GET /login?id=1 UNION SELECT password FROM users HTTP/1.1" 200 512'
    parser = CLFParser()
    entry = parser.parse_line(log_line)
    storage.ingest_batch([entry], 1)

    findings = analyzer.get_findings({"upload_id": 1})
    assert len(findings) > 0
    assert any(f["rule_id"] == "custom_sqli" for f in findings)

    overview = analyzer.get_overview({"upload_id": 1})
    assert overview["total_attacks"] > 0
    assert overview["suspicious_ips_count"] == 1

def test_xss_detection(storage, analyzer):
    log_line = '192.168.1.11 - - [22/Jun/2026:12:00:01 +0000] "GET /search?q=<script>alert(1)</script> HTTP/1.1" 200 512'
    parser = CLFParser()
    entry = parser.parse_line(log_line)
    storage.ingest_batch([entry], 2)

    findings = analyzer.get_findings({"upload_id": 2})
    assert len(findings) > 0
    assert any(f["rule_id"] == "custom_xss" for f in findings)

def test_directory_traversal_detection(storage, analyzer):
    log_line = '192.168.1.12 - - [22/Jun/2026:12:00:02 +0000] "GET /static/../../etc/passwd HTTP/1.1" 200 512'
    parser = CLFParser()
    entry = parser.parse_line(log_line)
    storage.ingest_batch([entry], 3)

    findings = analyzer.get_findings({"upload_id": 3})
    assert len(findings) > 0
    assert any(f["rule_id"] == "custom_path_traversal" for f in findings)

def test_command_injection_detection(storage, analyzer):
    log_line = '192.168.1.13 - - [22/Jun/2026:12:00:03 +0000] "GET /exec?cmd=ls%20-la;cat%20/etc/shadow HTTP/1.1" 200 512'
    parser = CLFParser()
    entry = parser.parse_line(log_line)
    storage.ingest_batch([entry], 4)

    findings = analyzer.get_findings({"upload_id": 4})
    assert len(findings) > 0
    assert any(f["rule_id"] == "custom_command_injection" for f in findings)

def test_malformed_request_payload_in_protocol(storage, analyzer):
    # Payload shifted to protocol field
    log_line = '192.168.1.14 - - [22/Jun/2026:12:00:04 +0000] "GET /index.html <script>alert(1)</script>" 200 512'
    parser = CLFParser()
    entry = parser.parse_line(log_line)
    assert entry is not None
    storage.ingest_batch([entry], 5)

    findings = analyzer.get_findings({"upload_id": 5})
    assert len(findings) > 0
    assert any(f["rule_id"] == "custom_xss" for f in findings)
