import pytest
from datetime import datetime, timedelta
from app.models.schema import NormalizedLogEntry
from app.analytics.engine import AnalyticsEngine
from app.storage.duckdb_storage import DuckDBStorage

@pytest.fixture
def engine():
    storage = DuckDBStorage(":memory:")
    eng = AnalyticsEngine(storage)

    # Generate some realistic test data
    base_time = datetime(2023, 1, 1, 12, 0, 0)
    entries = []

    # Session 1 (User A)
    entries.append(NormalizedLogEntry(
        timestamp=base_time, ip="192.168.1.1", method="GET", url="/home", status_code=200,
        bytes_sent=1024, response_time_ms=100.0, user_agent="Mozilla/5.0"
    ))
    entries.append(NormalizedLogEntry(
        timestamp=base_time + timedelta(minutes=5), ip="192.168.1.1", method="GET", url="/products/123", status_code=200,
        bytes_sent=2048, response_time_ms=250.0, user_agent="Mozilla/5.0"
    ))
    entries.append(NormalizedLogEntry(
        timestamp=base_time + timedelta(minutes=10), ip="192.168.1.1", method="GET", url="/checkout", status_code=200,
        bytes_sent=512, response_time_ms=500.0, user_agent="Mozilla/5.0"
    ))

    # Session 2 (User B - Bot)
    entries.append(NormalizedLogEntry(
        timestamp=base_time + timedelta(minutes=1), ip="10.0.0.1", method="GET", url="/about", status_code=404,
        bytes_sent=256, response_time_ms=50.0, user_agent="Googlebot/2.1"
    ))

    # Session 3 (User A returning later > 30 mins)
    entries.append(NormalizedLogEntry(
        timestamp=base_time + timedelta(hours=2), ip="192.168.1.1", method="GET", url="/home", status_code=200,
        bytes_sent=1024, response_time_ms=120.0, user_agent="Mozilla/5.0"
    ))

    # Error case (User C)
    entries.append(NormalizedLogEntry(
        timestamp=base_time + timedelta(hours=3), ip="172.16.0.1", method="POST", url="/login", status_code=500,
        bytes_sent=128, response_time_ms=1500.0, user_agent="curl/7.68.0"
    ))

    eng.ingest_entries(entries)
    yield eng
    storage.close()

def test_traffic_summary(engine):
    summary = engine.get_traffic_summary()
    assert summary["total_requests"] == 6
    assert summary["hits"] == 4
    assert summary["unique_visitors"] == 3
    assert summary["total_sessions"] == 4 # 2 for A, 1 for B, 1 for C
    assert summary["returning_visitors"] == 1 # User A
    assert summary["total_bytes"] == 1024 + 2048 + 512 + 256 + 1024 + 128

def test_time_analytics(engine):
    hourly = engine.get_time_analytics(resolution="hour")
    assert len(hourly) == 3 # 12:00, 14:00, 15:00
    assert hourly[0]["total_requests"] == 4 # The first 4 requests

def test_performance_analytics(engine):
    perf = engine.get_performance_analytics()
    # 50, 100, 120, 250, 500, 1500
    assert perf["median_response_time"] == 185.0 # (120+250)/2
    assert perf["p99_response_time"] > 500.0 # Will be closer to 1500

def test_url_analytics(engine):
    top_urls = engine.get_top_urls(limit=2)
    assert len(top_urls) == 2
    assert top_urls[0]["url"] == "/home"
    assert top_urls[0]["count"] == 2

    # Normalized URLs test
    top_norm_urls = engine.get_top_urls(limit=5, normalized=True)
    urls = [u["url"] for u in top_norm_urls]
    assert "/products/{id}" in urls

def test_entry_exit_pages(engine):
    pages = engine.get_entry_exit_pages()
    entries = pages["entry_pages"]
    exits = pages["exit_pages"]

    entry_urls = [e["url"] for e in entries]
    exit_urls = [e["url"] for e in exits]

    assert "/home" in entry_urls
    assert "/checkout" in exit_urls

def test_status_code_analytics(engine):
    status = engine.get_status_code_analytics()
    dist = {d["status_code"]: d["count"] for d in status["distribution"]}

    assert dist[200] == 4
    assert dist[404] == 1
    assert dist[500] == 1

    assert round(status["success_rate"], 2) == 66.67
    assert round(status["client_error_rate"], 2) == 16.67
    assert round(status["server_error_rate"], 2) == 16.67

def test_visitor_analytics(engine):
    visitors = engine.get_visitor_analytics()
    assert visitors["top_ips"][0]["ip"] == "192.168.1.1"
    assert visitors["top_ips"][0]["count"] == 4

def test_filters(engine):
    # Test Bot Filter
    summary = engine.get_traffic_summary(filters={"bot_classification": "search_engine_bot"})
    assert summary["total_requests"] == 1
    assert summary["unique_visitors"] == 1

def test_traffic_trends(engine):
    trends = engine.get_traffic_trends()
    assert len(trends["peak_hours"]) > 0
    assert len(trends["peak_days"]) > 0
    assert len(trends["moving_averages"]) > 0
    assert "growth_percent" in trends["traffic_growth"]
