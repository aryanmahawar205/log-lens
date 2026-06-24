import pytest
import os
import shutil
from app.analytics.engine import NativeAnalyticsProvider
from app.analytics.goaccess import GoAccessAnalyticsProvider
from app.storage.duckdb_storage import DuckDBStorage
from app.integration_manager import integration_manager
from app.config import config

@pytest.fixture
def storage():
    # Use a temporary file for the database to avoid side effects
    db_path = "data/test_analytics.duckdb"
    if os.path.exists(db_path):
        os.remove(db_path)
    storage = DuckDBStorage(db_path)
    yield storage
    storage.close()
    if os.path.exists(db_path):
        os.remove(db_path)

def test_provider_instantiation(storage):
    native = NativeAnalyticsProvider(storage=storage)
    # This should not raise TypeError anymore
    assert native is not None

    goaccess = GoAccessAnalyticsProvider(storage=storage)
    assert goaccess is not None

def test_integration_manager_status():
    status = integration_manager.get_tool_status()
    assert "goaccess" in status
    assert "duckdb" in status
    assert "sigma" in status
    assert status["duckdb"]["healthy"] is True

def test_config_loading():
    # Verify we can read the config
    provider = config.get("analytics.provider")
    assert provider in ["native", "goaccess"]

def test_native_provider_empty_results(storage):
    native = NativeAnalyticsProvider(storage=storage)
    summary = native.get_traffic_summary({"upload_id": 123})
    assert summary["total_requests"] == 0
    assert summary["unique_visitors"] == 0

def test_goaccess_provider_missing_file(storage):
    goaccess = GoAccessAnalyticsProvider(storage=storage)
    summary = goaccess.get_traffic_summary({"upload_id": 999999})
    assert summary["total_requests"] == 0
