from typing import List, Dict, Any, Optional
from app.models.schema import NormalizedLogEntry
from app.storage.base import BaseStorage
from app.storage.duckdb_storage import DuckDBStorage
from app.analytics.query_builder import QueryBuilder

class AnalyticsEngine:
    """
    Core analytics engine using DuckDB for high-performance log processing.
    """

    def __init__(self, storage: Optional[BaseStorage] = None):
        if storage is None:
            self.storage = DuckDBStorage()
        else:
            self.storage = storage

    def ingest_entries(self, entries: List[NormalizedLogEntry], upload_id: int = 0):
        """
        Ingest a list of NormalizedLogEntry objects into the engine.
        """
        self.storage.ingest_batch(entries, upload_id)

    def get_traffic_summary(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return high-level traffic metrics.
        - total requests
        - hits (status 200)
        - unique visitors (unique IPs)
        - sessions
        - returning visitors (IPs with > 1 session)
        - pages per session
        - average session duration
        - bandwidth consumption
        """
        if filters is None:
            filters = {}

        where_clause, params = QueryBuilder.build_filters(filters)

        # Traffic Summary Query
        query = f"""
            SELECT
                COUNT(*) as total_requests,
                SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as hits,
                COUNT(DISTINCT ip) as unique_visitors,
                SUM(bytes_sent) as total_bytes
            FROM log_entries
            {where_clause}
        """
        results = self.storage.execute_query(query, tuple(params))
        summary = results[0] if results else {
            "total_requests": 0, "hits": 0, "unique_visitors": 0, "total_bytes": 0
        }

        # Session Metrics
        session_query = f"""
            WITH session_stats AS (
                SELECT
                    session_id,
                    ip,
                    COUNT(*) as pages,
                    MAX(timestamp) - MIN(timestamp) as duration
                FROM log_sessions
                {where_clause}
                GROUP BY session_id, ip, upload_id
            ),
            user_stats AS (
                SELECT
                    ip,
                    COUNT(DISTINCT session_id) as session_count
                FROM session_stats
                GROUP BY ip
            )
            SELECT
                COUNT(session_id) as total_sessions,
                AVG(pages) as avg_pages_per_session,
                AVG(EXTRACT(EPOCH FROM duration)) as avg_session_duration_sec,
                (SELECT COUNT(*) FROM user_stats WHERE session_count > 1) as returning_visitors
            FROM session_stats
        """

        session_results = self.storage.execute_query(session_query, tuple(params))
        session_summary = session_results[0] if session_results else {
            "total_sessions": 0, "avg_pages_per_session": 0.0, "avg_session_duration_sec": 0.0, "returning_visitors": 0
        }

        # Handle null values that DuckDB might return
        return {
            "total_requests": summary.get("total_requests") or 0,
            "hits": summary.get("hits") or 0,
            "unique_visitors": summary.get("unique_visitors") or 0,
            "total_bytes": int(summary.get("total_bytes") or 0),
            "total_sessions": session_summary.get("total_sessions") or 0,
            "returning_visitors": session_summary.get("returning_visitors") or 0,
            "avg_pages_per_session": float(session_summary.get("avg_pages_per_session") or 0.0),
            "avg_session_duration_sec": float(session_summary.get("avg_session_duration_sec") or 0.0),
        }

    def get_time_analytics(self, resolution: str = 'hour', filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Return traffic grouped by time.
        resolution: 'minute', 'hour', 'day', 'month'
        """
        if filters is None:
            filters = {}

        where_clause, params = QueryBuilder.build_filters(filters)

        valid_resolutions = ['minute', 'hour', 'day', 'month']
        if resolution not in valid_resolutions:
            resolution = 'hour'

        query = f"""
            SELECT
                DATE_TRUNC('{resolution}', timestamp) as time_bucket,
                COUNT(*) as total_requests,
                COUNT(DISTINCT ip) as unique_visitors,
                SUM(bytes_sent) as total_bytes
            FROM log_entries
            {where_clause}
            GROUP BY time_bucket
            ORDER BY time_bucket ASC
        """
        return self.storage.execute_query(query, tuple(params))

    def get_performance_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return performance analytics.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        where_condition = where_clause + " AND response_time_ms IS NOT NULL" if where_clause else " WHERE response_time_ms IS NOT NULL"

        query = f"""
            SELECT
                AVG(response_time_ms) as avg_response_time,
                MEDIAN(response_time_ms) as median_response_time,
                QUANTILE_CONT(response_time_ms, 0.90) as p90_response_time,
                QUANTILE_CONT(response_time_ms, 0.95) as p95_response_time,
                QUANTILE_CONT(response_time_ms, 0.99) as p99_response_time
            FROM log_entries
            {where_condition}
        """
        results = self.storage.execute_query(query, tuple(params))
        metrics = results[0] if results else {}

        # Slowest endpoints
        slow_query = f"""
            SELECT normalized_url as url, AVG(response_time_ms) as avg_time, COUNT(*) as count
            FROM log_entries
            {where_condition}
            GROUP BY normalized_url
            HAVING COUNT(*) > 5
            ORDER BY avg_time DESC
            LIMIT 10
        """
        slowest = self.storage.execute_query(slow_query, tuple(params))

        return {
            "avg_response_time": metrics.get("avg_response_time") or 0.0,
            "median_response_time": metrics.get("median_response_time") or 0.0,
            "p90_response_time": metrics.get("p90_response_time") or 0.0,
            "p95_response_time": metrics.get("p95_response_time") or 0.0,
            "p99_response_time": metrics.get("p99_response_time") or 0.0,
            "slowest_endpoints": slowest
        }

    def get_top_urls(self, limit: int = 10, normalized: bool = False, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Return top URLs. If normalized=True, uses the normalized_url column.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        url_col = "normalized_url" if normalized else "url"

        query = f"""
            SELECT {url_col} as url, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY {url_col}
            ORDER BY count DESC
            LIMIT ?
        """
        return self.storage.execute_query(query, tuple(params) + (limit,))

    def get_entry_exit_pages(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return top entry and exit pages based on sessions.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        entry_query = f"""
            WITH ranked_sessions AS (
                SELECT session_id, url,
                       ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp ASC) as rn
                FROM log_sessions
                {where_clause}
            )
            SELECT url, COUNT(*) as count
            FROM ranked_sessions
            WHERE rn = 1
            GROUP BY url
            ORDER BY count DESC
            LIMIT ?
        """
        entry_pages = self.storage.execute_query(entry_query, tuple(params) + (limit,))

        exit_query = f"""
            WITH ranked_sessions AS (
                SELECT session_id, url,
                       ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp DESC) as rn
                FROM log_sessions
                {where_clause}
            )
            SELECT url, COUNT(*) as count
            FROM ranked_sessions
            WHERE rn = 1
            GROUP BY url
            ORDER BY count DESC
            LIMIT ?
        """
        exit_pages = self.storage.execute_query(exit_query, tuple(params) + (limit,))

        return {
            "entry_pages": entry_pages,
            "exit_pages": exit_pages
        }

    def get_status_code_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return status code analytics.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        dist_query = f"""
            SELECT status_code, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY status_code
            ORDER BY count DESC
        """
        distribution = self.storage.execute_query(dist_query, tuple(params))

        rates_query = f"""
            SELECT
                SUM(CASE WHEN status_code >= 200 AND status_code < 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as client_error_rate,
                SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as server_error_rate
            FROM log_entries
            {where_clause}
        """
        rates_results = self.storage.execute_query(rates_query, tuple(params))
        rates = rates_results[0] if rates_results else {
            "success_rate": 0.0, "client_error_rate": 0.0, "server_error_rate": 0.0
        }

        return {
            "distribution": distribution,
            "success_rate": rates.get("success_rate") or 0.0,
            "client_error_rate": rates.get("client_error_rate") or 0.0,
            "server_error_rate": rates.get("server_error_rate") or 0.0
        }

    def get_visitor_analytics(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return visitor analytics.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        ip_query = f"""
            SELECT ip, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY ip
            ORDER BY count DESC
            LIMIT ?
        """
        top_ips = self.storage.execute_query(ip_query, tuple(params) + (limit,))

        ua_query = f"""
            SELECT user_agent, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY user_agent
            ORDER BY count DESC
            LIMIT ?
        """
        top_uas = self.storage.execute_query(ua_query, tuple(params) + (limit,))

        return {
            "top_ips": top_ips,
            "top_user_agents": top_uas
        }

    def get_traffic_trends(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return traffic trends including peak hours/days and moving averages.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        peak_hours_query = f"""
            SELECT EXTRACT(HOUR FROM timestamp) as hour, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 5
        """
        peak_hours = self.storage.execute_query(peak_hours_query, tuple(params))

        peak_days_query = f"""
            SELECT DATE_TRUNC('day', timestamp) as day, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY day
            ORDER BY count DESC
            LIMIT 5
        """
        peak_days = self.storage.execute_query(peak_days_query, tuple(params))

        moving_avg_query = f"""
            WITH daily_counts AS (
                SELECT DATE_TRUNC('day', timestamp) as day, COUNT(*) as daily_requests
                FROM log_entries
                {where_clause}
                GROUP BY day
            )
            SELECT day, daily_requests,
                   AVG(daily_requests) OVER (
                       ORDER BY day
                       ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                   ) as moving_avg_7d
            FROM daily_counts
            ORDER BY day ASC
        """
        moving_averages = self.storage.execute_query(moving_avg_query, tuple(params))

        # Calculate simple growth comparing last 7 days vs previous 7 days if possible
        growth_query = f"""
            WITH periods AS (
                SELECT
                    SUM(CASE WHEN timestamp >= current_date - interval '7 days' THEN 1 ELSE 0 END) as last_7d,
                    SUM(CASE WHEN timestamp >= current_date - interval '14 days' AND timestamp < current_date - interval '7 days' THEN 1 ELSE 0 END) as prev_7d
                FROM log_entries
                {where_clause}
            )
            SELECT last_7d, prev_7d,
                   CASE WHEN prev_7d = 0 THEN 0 ELSE ((last_7d - prev_7d) * 100.0 / prev_7d) END as growth_percent
            FROM periods
        """
        growth_res = self.storage.execute_query(growth_query, tuple(params))
        growth = growth_res[0] if growth_res else {"last_7d": 0, "prev_7d": 0, "growth_percent": 0.0}

        return {
            "peak_hours": peak_hours,
            "peak_days": peak_days,
            "moving_averages": moving_averages,
            "traffic_growth": growth
        }

    def get_bounce_and_landing_pages(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return landing pages and bounce candidates.
        Landing pages are the first URL in a session.
        Bounce candidates are sessions that only hit a single page.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        # Same as entry pages
        landing_query = f"""
            WITH ranked_sessions AS (
                SELECT session_id, url,
                       ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp ASC) as rn
                FROM log_sessions
                {where_clause}
            )
            SELECT url, COUNT(*) as count
            FROM ranked_sessions
            WHERE rn = 1
            GROUP BY url
            ORDER BY count DESC
            LIMIT ?
        """
        landing_pages = self.storage.execute_query(landing_query, tuple(params) + (limit,))

        # Bounce candidates: sessions with exactly 1 page
        bounce_query = f"""
            WITH session_counts AS (
                SELECT session_id, MIN(url) as url, COUNT(*) as page_count
                FROM log_sessions
                {where_clause}
                GROUP BY session_id
                HAVING COUNT(*) = 1
            )
            SELECT url, COUNT(*) as bounce_count
            FROM session_counts
            GROUP BY url
            ORDER BY bounce_count DESC
            LIMIT ?
        """
        bounce_candidates = self.storage.execute_query(bounce_query, tuple(params) + (limit,))

        return {
            "landing_pages": landing_pages,
            "bounce_candidates": bounce_candidates
        }

    def get_extended_performance_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return extended performance metrics like fastest endpoints and throughput.
        """
        if filters is None:
            filters = {}
        where_condition = QueryBuilder.build_filters(filters)[0]
        params = QueryBuilder.build_filters(filters)[1]

        where_condition = where_condition + " AND response_time_ms IS NOT NULL" if where_condition else " WHERE response_time_ms IS NOT NULL"

        fast_query = f"""
            SELECT
                normalized_url as url,
                AVG(response_time_ms) as avg_time,
                QUANTILE_CONT(response_time_ms, 0.5) as median_time,
                QUANTILE_CONT(response_time_ms, 0.90) as p90_time,
                QUANTILE_CONT(response_time_ms, 0.95) as p95_time,
                QUANTILE_CONT(response_time_ms, 0.99) as p99_time,
                COUNT(*) as count
            FROM log_entries
            {where_condition}
            GROUP BY normalized_url
            HAVING COUNT(*) > 5
            ORDER BY avg_time ASC
            LIMIT 10
        """
        fastest = self.storage.execute_query(fast_query, tuple(params))

        # Throughput analysis: bytes sent over time
        throughput_query = f"""
            SELECT DATE_TRUNC('hour', timestamp) as hour_bucket, SUM(bytes_sent) as total_bytes, SUM(bytes_sent) / 3600.0 as bytes_per_second
            FROM log_entries
            {where_condition}
            GROUP BY hour_bucket
            ORDER BY hour_bucket ASC
        """
        throughput = self.storage.execute_query(throughput_query, tuple(params))

        return {
            "fastest_endpoints": fastest,
            "throughput_analysis": throughput
        }

    def get_status_code_groups(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Group status codes by endpoint, hour, and day.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        by_endpoint_query = f"""
            SELECT normalized_url, status_code, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY normalized_url, status_code
            ORDER BY count DESC
            LIMIT 50
        """
        by_endpoint = self.storage.execute_query(by_endpoint_query, tuple(params))

        by_hour_query = f"""
            SELECT EXTRACT(HOUR FROM timestamp) as hour, status_code, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY hour, status_code
            ORDER BY hour ASC
        """
        by_hour = self.storage.execute_query(by_hour_query, tuple(params))

        by_day_query = f"""
            SELECT DATE_TRUNC('day', timestamp) as day, status_code, COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY day, status_code
            ORDER BY day ASC
        """
        by_day = self.storage.execute_query(by_day_query, tuple(params))

        return {
            "by_endpoint": by_endpoint,
            "by_hour": by_hour,
            "by_day": by_day
        }

    def get_extended_visitor_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract browser and OS distribution from user agent strings via naive regex checks.
        """
        if filters is None:
            filters = {}
        where_clause, params = QueryBuilder.build_filters(filters)

        browser_query = f"""
            SELECT
                CASE
                    WHEN user_agent IS NULL OR user_agent = '' THEN 'Unknown'
                    WHEN user_agent ILIKE '%Chrome%' AND user_agent NOT ILIKE '%Edg%' THEN 'Chrome'
                    WHEN user_agent ILIKE '%Safari%' AND user_agent NOT ILIKE '%Chrome%' THEN 'Safari'
                    WHEN user_agent ILIKE '%Firefox%' THEN 'Firefox'
                    WHEN user_agent ILIKE '%Edg%' THEN 'Edge'
                    WHEN user_agent ILIKE '%Googlebot%' THEN 'Googlebot'
                    WHEN user_agent ILIKE '%curl%' THEN 'cURL'
                    ELSE 'Unknown'
                END as browser,
                COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY browser
            ORDER BY count DESC
        """
        browsers = self.storage.execute_query(browser_query, tuple(params))

        os_query = f"""
            SELECT
                CASE
                    WHEN user_agent IS NULL OR user_agent = '' THEN 'Unknown'
                    WHEN user_agent ILIKE '%Windows%' THEN 'Windows'
                    WHEN user_agent ILIKE '%Mac OS X%' THEN 'Mac OS'
                    WHEN user_agent ILIKE '%Linux%' AND user_agent NOT ILIKE '%Android%' THEN 'Linux'
                    WHEN user_agent ILIKE '%Android%' THEN 'Android'
                    WHEN user_agent ILIKE '%iPhone%' OR user_agent ILIKE '%iPad%' THEN 'iOS'
                    ELSE 'Unknown'
                END as os,
                COUNT(*) as count
            FROM log_entries
            {where_clause}
            GROUP BY os
            ORDER BY count DESC
        """
        operating_systems = self.storage.execute_query(os_query, tuple(params))

        return {
            "browser_distribution": browsers,
            "os_distribution": operating_systems
        }
