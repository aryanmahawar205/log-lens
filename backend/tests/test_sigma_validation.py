import pytest
from app.storage.duckdb_storage import DuckDBStorage
from app.security.sigma_engine import SigmaEngine
from app.models.schema import NormalizedLogEntry
from datetime import datetime

@pytest.fixture
def test_db():
    storage = DuckDBStorage(":memory:")
    yield storage
    storage.close()

def test_sigma_sqli(test_db):
    entries = [
        # SQLi in query string
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.10", method="GET", url="/product", query_string="id=1%20UNION%20SELECT", status_code=200, bytes_sent=0, user_agent="Mozilla"),
        # SQLi in url (malformed request parsed)
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.11", method="GET", url="/product?id=1 UNION SELECT", status_code=200, bytes_sent=0, user_agent="Mozilla"),
        # Normal request
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.12", method="GET", url="/product", query_string="id=1", status_code=200, bytes_sent=0, user_agent="Mozilla")
    ]
    test_db.ingest_batch(entries)

    engine = SigmaEngine("rules/sigma")
    findings = engine.execute(test_db)

    # We should have exactly 2 SQLi findings
    sqli_findings = [f for f in findings if f["rule_title"] == "SQL Injection Attempt"]
    assert len(sqli_findings) == 2
    ips = [f["ip"] for f in sqli_findings]
    assert "172.16.0.10" in ips
    assert "172.16.0.11" in ips
    assert "172.16.0.12" not in ips

def test_sigma_path_traversal(test_db):
    entries = [
        # PT in query string
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.10", method="GET", url="/download", query_string="file=../../../../etc/passwd", status_code=200, bytes_sent=0, user_agent="Mozilla"),
        # PT in url
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.11", method="GET", url="/../../../../etc/passwd", status_code=200, bytes_sent=0, user_agent="Mozilla"),
        # Normal request
        NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.12", method="GET", url="/download", query_string="file=report.pdf", status_code=200, bytes_sent=0, user_agent="Mozilla")
    ]
    test_db.ingest_batch(entries)

    engine = SigmaEngine("rules/sigma")
    findings = engine.execute(test_db)

    pt_findings = [f for f in findings if f["rule_title"] == "Path Traversal Attempt"]
    assert len(pt_findings) == 2
    ips = [f["ip"] for f in pt_findings]
    assert "172.16.0.10" in ips
    assert "172.16.0.11" in ips
    assert "172.16.0.12" not in ips

def test_sigma_diagnostics(test_db):
    engine = SigmaEngine("rules/sigma")
    engine.execute(test_db)

    diag = engine.get_diagnostics()
    assert diag["enabled"] is True
    assert diag["provider_status"] == "active"
    assert diag["execution_count"] == 1
    assert diag["loaded_rules"] > 0
