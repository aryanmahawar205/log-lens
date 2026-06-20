import sqlite3
from typing import List, Dict, Any
from app.models.schema import NormalizedLogEntry
from app.storage.base import BaseStorage
from app.normalization.url import URLNormalizer
from app.bot_detection.detector import BotDetector

class SQLiteStorage(BaseStorage):
    """
    SQLite-backed storage for environments where DuckDB is unavailable.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self):
        """Initialize the schema for normalized logs."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_entries (
                timestamp DATETIME,
                ip TEXT,
                method TEXT,
                url TEXT,
                query_string TEXT,
                status_code INTEGER,
                bytes_sent INTEGER,
                request_size_bytes INTEGER,
                response_time_ms REAL,
                referrer TEXT,
                user_agent TEXT,
                host TEXT,
                virtual_host TEXT,
                protocol TEXT,
                normalized_url TEXT,
                bot_classification TEXT
            )
        """)

        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON log_entries(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip ON log_entries(ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_code ON log_entries(status_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_classification ON log_entries(bot_classification)")

        # Create view for sessionization (SQLite requires window functions, available in sqlite 3.25+)
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS log_sessions AS
            WITH session_groups AS (
                SELECT
                    *,
                    SUM(CASE WHEN prev_time IS NULL OR (julianday(timestamp) - julianday(prev_time)) * 86400 > 1800 THEN 1 ELSE 0 END)
                    OVER (PARTITION BY ip, user_agent ORDER BY timestamp) AS session_id_num
                FROM (
                    SELECT
                        *,
                        LAG(timestamp) OVER (PARTITION BY ip, user_agent ORDER BY timestamp) AS prev_time
                    FROM log_entries
                )
            )
            SELECT
                *,
                ip || '-' || coalesce(user_agent, 'unknown') || '-' || CAST(session_id_num AS TEXT) AS session_id
            FROM session_groups
        """)
        self.conn.commit()

    def ingest_batch(self, entries: List[NormalizedLogEntry]):
        """Ingest a batch of NormalizedLogEntry objects into SQLite."""
        if not entries:
            return

        data = []
        for entry in entries:
            normalized_url = URLNormalizer.normalize(entry.url)
            bot_classification = BotDetector.classify(entry.user_agent)
            data.append((
                entry.timestamp.isoformat(),
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

        cursor = self.conn.cursor()
        cursor.executemany("""
            INSERT INTO log_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        self.conn.commit()

    def execute_query(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results as dictionaries."""
        cursor = self.conn.cursor()
        cursor.execute(query, parameters)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()
