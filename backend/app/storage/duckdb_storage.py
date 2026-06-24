import duckdb
from typing import List, Dict, Any
from app.models.schema import NormalizedLogEntry
from app.storage.base import BaseStorage
from app.normalization.url import URLNormalizer
from app.bot_detection.detector import BotDetector
import os

class DuckDBStorage(BaseStorage):
    """
    DuckDB-backed storage for high-performance analytics.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = duckdb.connect(database=self.db_path)
        self.initialize()

    def initialize(self):
        """Initialize the schema for normalized logs and views."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id BIGINT PRIMARY KEY,
                filename VARCHAR,
                format VARCHAR,
                uploaded_at TIMESTAMP,
                total_entries BIGINT,
                parser_used VARCHAR,
                confidence DOUBLE
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS log_entries (
                upload_id BIGINT,
                timestamp TIMESTAMP,
                ip VARCHAR,
                method VARCHAR,
                url VARCHAR,
                query_string VARCHAR,
                status_code INTEGER,
                bytes_sent BIGINT,
                request_size_bytes BIGINT,
                response_time_ms DOUBLE,
                referrer VARCHAR,
                user_agent VARCHAR,
                host VARCHAR,
                virtual_host VARCHAR,
                protocol VARCHAR,
                normalized_url VARCHAR,
                bot_classification VARCHAR
            )
        """)

        # Create indices for common filtering columns
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_upload_id ON log_entries(upload_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON log_entries(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ip ON log_entries(ip)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_status_code ON log_entries(status_code)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_bot_classification ON log_entries(bot_classification)")

        # Persistent execution logs for external tools
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS external_tool_executions (
                id INTEGER PRIMARY KEY,
                tool_name VARCHAR,
                upload_id BIGINT,
                status VARCHAR,
                execution_timestamp TIMESTAMP,
                duration_sec DOUBLE,
                version VARCHAR,
                artifacts JSON
            )
        """)
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_execution_id START 1")

        # Create view for sessionization (30 min timeout)
        self.conn.execute("""
            CREATE OR REPLACE VIEW log_sessions AS
            WITH base_logs AS (
                SELECT *,
                       COALESCE(user_agent, 'unknown') as ua_fixed
                FROM log_entries
            ),
            prev_times AS (
                SELECT
                    *,
                    LAG(timestamp) OVER (PARTITION BY upload_id, ip, ua_fixed ORDER BY timestamp) AS prev_time
                FROM base_logs
            ),
            session_markers AS (
                SELECT
                    *,
                    CASE WHEN prev_time IS NULL OR epoch(timestamp) - epoch(prev_time) > 1800 THEN 1 ELSE 0 END AS is_new_session
                FROM prev_times
            ),
            session_groups AS (
                SELECT
                    *,
                    SUM(is_new_session) OVER (PARTITION BY upload_id, ip, ua_fixed ORDER BY timestamp) AS session_id_num
                FROM session_markers
            )
            SELECT
                *,
                COALESCE(upload_id, 0) || '-' || ip || '-' || ua_fixed || '-' || session_id_num AS session_id
            FROM session_groups
        """)

    def ingest_batch(self, entries: List[NormalizedLogEntry], upload_id: int = 0):
        """Ingest a batch of NormalizedLogEntry objects into DuckDB."""
        if not entries:
            return

        data = []
        for entry in entries:
            normalized_url = URLNormalizer.normalize(entry.url)
            bot_classification = BotDetector.classify(entry.user_agent)
            data.append((
                upload_id,
                entry.timestamp,
                entry.ip,
                entry.method,
                entry.url,
                entry.query_string,
                entry.status_code,
                entry.bytes_sent,
                entry.request_size_bytes,
                entry.response_time_ms,
                entry.referrer,
                entry.user_agent,
                entry.host,
                entry.virtual_host,
                entry.protocol,
                normalized_url,
                bot_classification
            ))

        self.conn.executemany("""
            INSERT INTO log_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

    def execute_query(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results as dictionaries."""
        cursor = self.conn.execute(query, parameters)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()
