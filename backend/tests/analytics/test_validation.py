import pytest
import os
import json
from app.analytics.engine import AnalyticsEngine
from app.parsers.apache import ApacheAccessParser
from app.storage.duckdb_storage import DuckDBStorage

def test_validation_framework():
    # Setup test DB
    storage = DuckDBStorage(":memory:")
    engine = AnalyticsEngine(storage=storage)
    parser = ApacheAccessParser()

    # Read expected results
    results_path = os.path.join(os.path.dirname(__file__), "../expected_results.json")
    with open(results_path, 'r') as f:
        expected = json.load(f)

    # Ingest test log
    log_path = os.path.join(os.path.dirname(__file__), "../sample_logs/tiny_6_line.log")

    entries = []
    for entry in parser.parse_file(log_path):
        entries.append(entry)

    # Upload ID 999 for test
    engine.ingest_entries(entries, upload_id=999)

    # Validate metrics
    summary = engine.get_traffic_summary({"upload_id": 999})
    expected_tiny = expected["tiny_6_line.log"]

    assert summary["total_requests"] == expected_tiny["total_requests"]
    assert summary["unique_visitors"] == expected_tiny["unique_visitors"]
    assert summary["total_sessions"] == expected_tiny["sessions"]
