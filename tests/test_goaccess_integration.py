import pytest
import os
import shutil
import json
from app.analytics.engine import NativeAnalyticsProvider
from app.analytics.goaccess import GoAccessAnalyticsProvider
from app.storage.duckdb_storage import DuckDBStorage
from app.models.schema import NormalizedLogEntry
from datetime import datetime

@pytest.fixture
def storage():
    db_path = "data/test_integration.duckdb"
    if os.path.exists(db_path):
        os.remove(db_path)
    storage = DuckDBStorage(db_path)

    # Initialize uploads table if it doesn't exist (DuckDBStorage should handle it usually)
    storage.execute_query("CREATE TABLE IF NOT EXISTS uploads (id BIGINT, filename VARCHAR, format VARCHAR, uploaded_at TIMESTAMP, total_entries INTEGER, parser_used VARCHAR, confidence DOUBLE)")

    yield storage
    storage.close()
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def sample_log(storage):
    upload_id = 1
    log_content = '127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326 "-" "Mozilla/5.0"\n'
    log_dir = "data/raw_logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{upload_id}.log")
    with open(log_path, "w") as f:
        f.write(log_content)

    storage.execute_query(
        "INSERT INTO uploads (id, filename, format, uploaded_at, total_entries, parser_used, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (upload_id, "test.log", "apache_access", datetime.now(), 1, "apache_access", 1.0)
    )

    # Also ingest into DuckDB for comparison
    entry = NormalizedLogEntry(
        timestamp=datetime(2023, 10, 10, 13, 55, 36),
        ip="127.0.0.1",
        method="GET",
        url="/index.html",
        status_code=200,
        bytes_sent=2326,
        user_agent="Mozilla/5.0"
    )
    storage.ingest_batch([entry], upload_id)

    yield upload_id

    if os.path.exists(log_path):
        os.remove(log_path)

def test_goaccess_fallback_when_binary_missing(storage, sample_log, monkeypatch):
    # Simulate missing goaccess binary
    monkeypatch.setattr(shutil, "which", lambda x: None)

    native = NativeAnalyticsProvider(storage=storage)
    goaccess = GoAccessAnalyticsProvider(storage=storage, fallback_provider=native)

    summary = goaccess.get_traffic_summary({"upload_id": sample_log})
    assert summary["total_requests"] == 1
    assert summary["hits"] == 1
    assert summary["unique_visitors"] == 1

def test_goaccess_consistency_check(storage, sample_log):
    if not shutil.which("goaccess"):
        pytest.skip("GoAccess not installed")

    native = NativeAnalyticsProvider(storage=storage)
    goaccess = GoAccessAnalyticsProvider(storage=storage, fallback_provider=native)

    native_summary = native.get_traffic_summary({"upload_id": sample_log})
    goaccess_summary = goaccess.get_traffic_summary({"upload_id": sample_log})

    assert goaccess_summary["total_requests"] == native_summary["total_requests"]
    assert goaccess_summary["hits"] == native_summary["hits"]
    assert goaccess_summary["unique_visitors"] == native_summary["unique_visitors"]
    assert goaccess_summary["total_bytes"] == native_summary["total_bytes"]

def test_goaccess_unsupported_method_fallback(storage, sample_log):
    native = NativeAnalyticsProvider(storage=storage)
    goaccess = GoAccessAnalyticsProvider(storage=storage, fallback_provider=native)

    # This method is not implemented in GoAccess and should fallback
    trends = goaccess.get_traffic_trends({"upload_id": sample_log})
    assert "peak_hours" in trends
    assert len(trends["peak_hours"]) > 0

def test_goaccess_invalid_log_format(storage):
    upload_id = 999
    log_dir = "data/raw_logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{upload_id}.log")
    with open(log_path, "w") as f:
        f.write("INVALID LOG LINE\n")

    storage.execute_query(
        "INSERT INTO uploads (id, filename, format, uploaded_at, total_entries, parser_used, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (upload_id, "invalid.log", "apache_access", datetime.now(), 1, "apache_access", 1.0)
    )

    native = NativeAnalyticsProvider(storage=storage)
    goaccess = GoAccessAnalyticsProvider(storage=storage, fallback_provider=native)

    # Should not crash, and preferably fallback or return empty
    summary = goaccess.get_traffic_summary({"upload_id": upload_id})
    assert "total_requests" in summary

    if os.path.exists(log_path):
        os.remove(log_path)
