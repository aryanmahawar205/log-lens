import pytest
import os
from app.storage.duckdb_storage import DuckDBStorage
from app.security.sigma_engine import SigmaEngine
from app.models.schema import NormalizedLogEntry
from datetime import datetime

@pytest.fixture
def test_db():
    storage = DuckDBStorage(":memory:")
    yield storage
    storage.close()

def test_sigma_reload(test_db):
    engine = SigmaEngine("rules/sigma")
    # Base count
    base_count = len(engine.get_rules())

    # Add a new rule dynamically
    new_rule_path = "rules/sigma/test_rule.yml"
    with open(new_rule_path, "w") as f:
        f.write("""
title: Test XSS
id: test-xss-123
status: experimental
description: Test XSS
logsource:
    category: webserver
detection:
    selection:
        url|contains:
            - 'script'
    condition: selection
level: high
""")

    try:
        engine.load_rules()
        assert len(engine.get_rules()) == base_count + 1

        rule = engine.get_rule("test-xss-123")
        assert rule is not None

        entries = [
            NormalizedLogEntry(timestamp=datetime.now(), ip="1.1.1.1", method="GET", url="/search?q=<script>", status_code=200, bytes_sent=0, user_agent="Mozilla")
        ]
        test_db.ingest_batch(entries)

        findings = engine.execute(test_db)
        assert any(f["rule_id"] == "test-xss-123" for f in findings)
    finally:
        os.remove(new_rule_path)
        engine.load_rules()
        assert len(engine.get_rules()) == base_count
