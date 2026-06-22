import pytest
from app.storage.duckdb_storage import DuckDBStorage
from app.security.analyzer import SecurityAnalyzer
from app.models.schema import NormalizedLogEntry
from datetime import datetime

@pytest.fixture
def test_db():
    storage = DuckDBStorage(":memory:")
    yield storage
    storage.close()

def test_security_analyzer_detections(test_db):
    entries = [
        # Directory enum
        NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/admin", status_code=404, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/.git", status_code=404, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/.env", status_code=404, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/backup", status_code=404, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/config", status_code=404, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/phpmyadmin", status_code=404, bytes_sent=0, user_agent="Mozilla"),

        # Brute force
        NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),

        # SQLi
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.10", method="GET", url="/product", query_string="id=1%20UNION%20SELECT", status_code=200, bytes_sent=0, user_agent="Mozilla"),

        # XSS
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.10", method="GET", url="/search", query_string="q=%3Cscript%3Ealert(1)%3C/script%3E", status_code=200, bytes_sent=0, user_agent="Mozilla"),

        # Scanner
        NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.99", method="GET", url="/", status_code=200, bytes_sent=0, user_agent="sqlmap/1.5.8"),

        # Command Injection
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.11", method="GET", url="/ping", query_string="ip=127.0.0.1;cat /etc/passwd", status_code=200, bytes_sent=0, user_agent="Mozilla"),

        # Path Traversal
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.12", method="GET", url="/download", query_string="file=../../../../etc/passwd", status_code=200, bytes_sent=0, user_agent="Mozilla")
    ]
    test_db.ingest_batch(entries)

    analyzer = SecurityAnalyzer(test_db)

    findings = analyzer.get_findings()
    assert len(findings) >= 7, f"Should detect at least 7 attacks, got {len(findings)}"

    types = [f["type"] for f in findings]
    assert "directory_enumeration" in types
    assert "brute_force" in types
    assert "sql_injection" in types
    assert "xss" in types
    assert "scanner" in types
    assert "command_injection" in types
    assert "path_traversal" in types

    ips = analyzer.get_suspicious_ips()
    assert len(ips) == 6

    # Check overview
    overview = analyzer.get_overview()
    assert overview["total_attacks"] == len(findings)
    assert overview["suspicious_ips_count"] == 6
