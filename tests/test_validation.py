import pytest
from datetime import datetime, timedelta
from app.models.schema import NormalizedLogEntry
from app.storage.duckdb_storage import DuckDBStorage
from app.analytics.engine import AnalyticsEngine

@pytest.fixture
def storage():
    return DuckDBStorage(":memory:")

@pytest.fixture
def engine(storage):
    return AnalyticsEngine(storage=storage)

def test_analytics_validation(engine, storage):
    # Create synthetic dataset
    # 10 requests total
    # 2 unique visitors (IP1, IP2)
    # 3 sessions:
    #   IP1: Session 1 (2 pages), Session 2 (1 page, 1 hour later)
    #   IP2: Session 3 (3 pages)
    # Status codes: 8x 200, 1x 404, 1x 500
    # Bandwidth: 10 * 100 = 1000 bytes

    base_time = datetime(2023, 10, 1, 10, 0, 0)
    upload_id = 12345

    entries = [
        # IP1 Session 1
        NormalizedLogEntry(timestamp=base_time, ip="1.1.1.1", method="GET", url="/", status_code=200, bytes_sent=100, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=base_time + timedelta(minutes=5), ip="1.1.1.1", method="GET", url="/about", status_code=200, bytes_sent=100, user_agent="Mozilla"),

        # IP1 Session 2 (65 min later > 30 min timeout)
        NormalizedLogEntry(timestamp=base_time + timedelta(minutes=70), ip="1.1.1.1", method="GET", url="/contact", status_code=200, bytes_sent=100, user_agent="Mozilla"),

        # IP2 Session 3
        NormalizedLogEntry(timestamp=base_time, ip="2.2.2.2", method="GET", url="/", status_code=200, bytes_sent=100, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=base_time + timedelta(minutes=2), ip="2.2.2.2", method="GET", url="/products", status_code=200, bytes_sent=100, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=base_time + timedelta(minutes=4), ip="2.2.2.2", method="GET", url="/cart", status_code=404, bytes_sent=100, user_agent="Mozilla"),

        # More requests to fill up
        NormalizedLogEntry(timestamp=base_time + timedelta(minutes=10), ip="2.2.2.2", method="POST", url="/checkout", status_code=500, bytes_sent=100, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=base_time + timedelta(minutes=15), ip="1.1.1.1", method="GET", url="/", status_code=200, bytes_sent=100, user_agent="Mozilla"), # This belongs to IP1 Session 1 (within 30m of /about)
        NormalizedLogEntry(timestamp=base_time + timedelta(minutes=20), ip="1.1.1.1", method="GET", url="/blog", status_code=200, bytes_sent=100, user_agent="Mozilla"),
        NormalizedLogEntry(timestamp=base_time + timedelta(minutes=25), ip="1.1.1.1", method="GET", url="/post1", status_code=200, bytes_sent=100, user_agent="Mozilla"),
    ]

    engine.ingest_entries(entries, upload_id)

    filters = {"upload_id": upload_id}
    summary = engine.get_traffic_summary(filters)

    assert summary["total_requests"] == 10
    assert summary["hits"] == 8
    assert summary["unique_visitors"] == 2
    assert summary["total_bytes"] == 1000

    # Sessions:
    # IP1:
    #   10:00:00 (/)
    #   10:05:00 (/about)
    #   10:15:00 (/) -> still session 1
    #   10:20:00 (/blog) -> still session 1
    #   10:25:00 (/post1) -> still session 1
    #   11:10:00 (/contact) -> session 2
    # IP2:
    #   10:00:00 (/)
    #   10:02:00 (/products)
    #   10:04:00 (/cart)
    #   10:10:00 (/checkout)
    # Total sessions = 3

    assert summary["total_sessions"] == 3
    # IP2: 10:00, 10:02, 10:04, 10:10. All within 30 min of previous. So 1 session.
    # IP1: Session 1 (10:00, 10:05, 10:15, 10:20, 10:25), Session 2 (11:10). 2 sessions.
    # Returning visitors = IPs with > 1 session. Only IP1. So returning_visitors should be 1.
    assert summary["returning_visitors"] == 1

    status_analytics = engine.get_status_code_analytics(filters)
    assert status_analytics["success_rate"] == 80.0
    assert status_analytics["client_error_rate"] == 10.0
    assert status_analytics["server_error_rate"] == 10.0

def test_apache_format_validation(engine):
    upload_id = 111
    # Apache Combined Format
    line = '127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 123 "http://referer.com" "Mozilla/5.0"'
    from app.parsers.apache import ApacheAccessParser
    parser = ApacheAccessParser()
    entry = parser.parse_line(line)
    assert entry is not None
    engine.ingest_entries([entry], upload_id)

    summary = engine.get_traffic_summary({"upload_id": upload_id})
    assert summary["total_requests"] == 1
    assert summary["unique_visitors"] == 1
    assert summary["total_bytes"] == 123

def test_nginx_format_validation(engine):
    upload_id = 222
    # Nginx Combined Format
    line = '192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "POST /api/data HTTP/1.1" 201 456 "-" "curl/7.68.0"'
    from app.parsers.nginx_access import NginxAccessParser
    parser = NginxAccessParser()
    entry = parser.parse_line(line)
    assert entry is not None
    engine.ingest_entries([entry], upload_id)

    summary = engine.get_traffic_summary({"upload_id": upload_id})
    assert summary["total_requests"] == 1
    assert summary["total_bytes"] == 456

def test_iis_format_validation(engine):
    upload_id = 333
    # IIS W3C Format
    line = '2023-10-10 13:55:36 10.0.0.1 GET /index.html - 80 - 192.168.1.1 Mozilla/5.0 - 200 0 0 15'
    from app.parsers.iis import IISW3CParser
    parser = IISW3CParser()
    entry = parser.parse_line(line)
    assert entry is not None
    assert entry.response_time_ms == 15
    engine.ingest_entries([entry], upload_id)

    perf = engine.get_performance_analytics({"upload_id": upload_id})
    assert perf["avg_response_time"] == 15

def test_json_format_validation(engine):
    upload_id = 444
    line = '{"ip": "8.8.8.8", "method": "GET", "url": "/json", "status": 200, "bytes": 789, "timestamp": "2023-10-10T13:55:36Z"}'
    from app.parsers.inference import InferenceParser
    parser = InferenceParser()
    entry = parser.parse_line(line)
    assert entry is not None
    assert entry.ip == "8.8.8.8"
    engine.ingest_entries([entry], upload_id)

    summary = engine.get_traffic_summary({"upload_id": upload_id})
    assert summary["total_requests"] == 1
    assert summary["total_bytes"] == 789

def test_security_attack_validation(engine, storage):
    upload_id = 555
    from app.security.analyzer import SecurityAnalyzer
    analyzer = SecurityAnalyzer(storage)

    entries = [
        NormalizedLogEntry(timestamp=datetime.now(), ip="9.9.9.9", method="GET", url="/admin", status_code=404, bytes_sent=0, user_agent="Nikto"),
        NormalizedLogEntry(timestamp=datetime.now(), ip="9.9.9.9", method="GET", url="/login?user=' OR 1=1--", status_code=200, bytes_sent=0, user_agent="Mozilla"),
    ]
    engine.ingest_entries(entries, upload_id)

    findings = analyzer.get_findings({"upload_id": upload_id})
    # Should detect Nikto (scanner) and SQLi (via custom or sigma)
    types = [f["rule_id"] for f in findings]
    assert any("scanner" in t for t in types)
    assert any("sqli" in t for t in types)
