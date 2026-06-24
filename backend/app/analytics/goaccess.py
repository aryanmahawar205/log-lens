import subprocess
import json
import os
import tempfile
import shutil
import time
from typing import Dict, Any, Optional, List
from app.analytics.base import AnalyticsProvider
from app.storage.base import BaseStorage
from app.storage.duckdb_storage import DuckDBStorage
from datetime import datetime

class GoAccessAnalyticsProvider(AnalyticsProvider):
    """
    Analytics provider using GoAccess for log processing.
    """

    def __init__(self, storage: Optional[BaseStorage] = None, fallback_provider: Optional[AnalyticsProvider] = None):
        if storage is None:
            self.storage = DuckDBStorage()
        else:
            self.storage = storage
        self.fallback_provider = fallback_provider
        self.log_dir = "data/raw_logs"
        os.makedirs(self.log_dir, exist_ok=True)

    def _get_log_path(self, upload_id: int) -> Optional[str]:
        path = os.path.join(self.log_dir, f"{upload_id}.log")
        if os.path.exists(path):
            return path
        return None

    def _get_log_format(self, upload_id: int) -> str:
        """
        Determine log format for GoAccess based on detected parser.
        GoAccess standard formats: COMBINED, COMMON, VCOMBINED, W3C, SQUID, CLOUD FRONT, GCS, AWSELB, AWSS3, AWSALB.
        """
        # Fetch format from storage
        result = self.storage.execute_query("SELECT format FROM uploads WHERE id = ?", (upload_id,))
        if not result:
            return "COMBINED"

        fmt = result[0]["format"].lower()

        # Mapping LogLens formats to GoAccess formats
        mapping = {
            "apache_access": "COMBINED",
            "nginx_access": "COMBINED",
            "clf": "COMMON",
            "iis_w3c": "W3C",
        }

        return mapping.get(fmt, "COMBINED")

    def _run_goaccess(self, upload_id: int) -> Optional[Dict[str, Any]]:
        from app.integration_manager import integration_manager
        log_path = self._get_log_path(upload_id)
        if not log_path:
            return None

        # Check if goaccess is installed
        if not shutil.which("goaccess"):
            integration_manager.record_execution("goaccess", "failed", 0, {"error": "Binary not found"})
            return None

        log_format = self._get_log_format(upload_id)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_name = tmp.name

        start_time = time.time()
        artifact_dir = f"data/artifacts/goaccess/{upload_id}"
        os.makedirs(artifact_dir, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_artifact = os.path.join(artifact_dir, f"report_{timestamp_str}.json")
        html_artifact = os.path.join(artifact_dir, f"report_{timestamp_str}.html")

        try:
            cmd = [
                "goaccess",
                log_path,
                f"--log-format={log_format}",
                f"--output={json_artifact}",
                f"--output={html_artifact}",
                "--no-global-config"
            ]
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            duration = time.time() - start_time

            with open(json_artifact, 'r') as f:
                data = json.load(f)

            version = "unknown"
            try:
                version = subprocess.check_output(["goaccess", "--version"]).decode().split("\n")[0].replace("GoAccess - ", "")
            except: pass

            # Persist to integration manager
            integration_manager.record_execution("goaccess", "success", duration, {
                "version": version,
                "json_artifact": json_artifact,
                "html_artifact": html_artifact,
                "log_format": log_format
            })

            # Persist to storage
            artifacts_json = json.dumps({
                "json": json_artifact,
                "html": html_artifact
            })
            self.storage.execute_query("""
                INSERT INTO external_tool_executions (id, tool_name, upload_id, status, execution_timestamp, duration_sec, version, artifacts)
                VALUES (nextval('seq_execution_id'), 'goaccess', ?, 'success', ?, ?, ?, ?)
            """, (upload_id, datetime.now(), duration, version, artifacts_json))

            return data
        except Exception as e:
            duration = time.time() - start_time
            print(f"Error running GoAccess: {e}")
            integration_manager.record_execution("goaccess", "failed", duration, {"error": str(e)})

            self.storage.execute_query("""
                INSERT INTO external_tool_executions (id, tool_name, upload_id, status, execution_timestamp, duration_sec, version, artifacts)
                VALUES (nextval('seq_execution_id'), 'goaccess', ?, 'failed', ?, ?, ?, ?)
            """, (upload_id, datetime.now(), duration, "unknown", json.dumps({"error": str(e)})))
            return None
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def get_traffic_summary(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        upload_id = filters.get("upload_id") if filters else None
        if not upload_id:
            return {
                "total_requests": 0, "hits": 0, "unique_visitors": 0, "total_bytes": 0,
                "total_sessions": 0, "returning_visitors": 0, "avg_pages_per_session": 0.0, "avg_session_duration_sec": 0.0
            }

        data = self._run_goaccess(upload_id)
        if not data and self.fallback_provider:
            return self.fallback_provider.get_traffic_summary(filters)

        if not data:
            return {
                "total_requests": 0, "hits": 0, "unique_visitors": 0, "total_bytes": 0,
                "total_sessions": 0, "returning_visitors": 0, "avg_pages_per_session": 0.0, "avg_session_duration_sec": 0.0
            }

        general = data.get("general", {})

        return {
            "total_requests": general.get("total_requests", 0),
            "hits": general.get("valid_requests", 0),
            "unique_visitors": general.get("unique_visitors", 0),
            "total_bytes": general.get("bandwidth", 0),
            "total_sessions": general.get("unique_visitors", 0),
            "returning_visitors": 0, # GoAccess doesn't easily provide this in summary
            "avg_pages_per_session": 0.0,
            "avg_session_duration_sec": 0.0,
        }

    def get_time_analytics(self, resolution: str = 'hour', filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        upload_id = filters.get("upload_id") if filters else None
        if not upload_id: return []

        data = self._run_goaccess(upload_id)
        if not data and self.fallback_provider:
            return self.fallback_provider.get_time_analytics(resolution, filters)

        if not data: return []

        results = []
        if resolution == 'day':
            for entry in data.get("visitors", {}).get("data", []):
                results.append({
                    "time_bucket": entry["data"],
                    "total_requests": entry["hits"]["count"],
                    "unique_visitors": entry["visitors"]["count"],
                    "total_bytes": entry["bw"]["count"]
                })
        else: # Default to hour
            for entry in data.get("hours", {}).get("data", []):
                results.append({
                    "time_bucket": entry["data"],
                    "total_requests": entry["hits"]["count"],
                    "unique_visitors": entry["visitors"]["count"],
                    "total_bytes": entry["bw"]["count"]
                })
        return results

    def get_performance_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.fallback_provider:
            return self.fallback_provider.get_performance_analytics(filters)

        return {
            "avg_response_time": 0.0, "median_response_time": 0.0,
            "p90_response_time": 0.0, "p95_response_time": 0.0, "p99_response_time": 0.0,
            "slowest_endpoints": []
        }

    def get_top_urls(self, limit: int = 10, normalized: bool = False, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        upload_id = filters.get("upload_id") if filters else None
        if not upload_id: return []

        data = self._run_goaccess(upload_id)
        if not data and self.fallback_provider:
            return self.fallback_provider.get_top_urls(limit, normalized, filters)

        if not data: return []

        requests = data.get("requests", {}).get("data", [])

        return [{"url": r["data"], "count": r["hits"]["count"]} for r in requests[:limit]]

    def get_entry_exit_pages(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        if self.fallback_provider:
            return self.fallback_provider.get_entry_exit_pages(limit, filters)

        return {"entry_pages": [], "exit_pages": []}

    def get_visitor_analytics(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        upload_id = filters.get("upload_id") if filters else None
        if not upload_id: return {"top_ips": [], "top_user_agents": []}

        data = self._run_goaccess(upload_id)
        if not data and self.fallback_provider:
            return self.fallback_provider.get_visitor_analytics(limit, filters)

        if not data: return {"top_ips": [], "top_user_agents": []}

        hosts = data.get("hosts", {}).get("data", [])

        return {
            "top_ips": [{"ip": h["data"], "count": h["hits"]["count"]} for h in hosts[:limit]],
            "top_user_agents": [] # GoAccess doesn't provide top UAs in this format easily
        }

    def get_status_code_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        upload_id = filters.get("upload_id") if filters else None
        if not upload_id: return {"distribution": [], "success_rate": 0, "client_error_rate": 0, "server_error_rate": 0}

        data = self._run_goaccess(upload_id)
        if not data and self.fallback_provider:
            return self.fallback_provider.get_status_code_analytics(filters)

        if not data: return {"distribution": [], "success_rate": 0, "client_error_rate": 0, "server_error_rate": 0}

        codes = data.get("status_codes", {}).get("data", [])

        dist = [{"status_code": int(c["data"]), "count": c["hits"]["count"]} for c in codes]

        total = sum(d["count"] for d in dist)
        if total == 0: return {"distribution": dist, "success_rate": 0, "client_error_rate": 0, "server_error_rate": 0}

        success = sum(d["count"] for d in dist if 200 <= d["status_code"] < 400)
        client_err = sum(d["count"] for d in dist if 400 <= d["status_code"] < 500)
        server_err = sum(d["count"] for d in dist if d["status_code"] >= 500)

        return {
            "distribution": dist,
            "success_rate": (success * 100.0 / total),
            "client_error_rate": (client_err * 100.0 / total),
            "server_error_rate": (server_err * 100.0 / total)
        }

    def get_traffic_trends(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.fallback_provider:
            return self.fallback_provider.get_traffic_trends(filters)

        return {"peak_hours": [], "peak_days": [], "moving_averages": [], "traffic_growth": {}}

    def get_bounce_and_landing_pages(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        if self.fallback_provider:
            return self.fallback_provider.get_bounce_and_landing_pages(limit, filters)

        return {"landing_pages": [], "bounce_candidates": []}

    def get_extended_performance_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.fallback_provider:
            return self.fallback_provider.get_extended_performance_analytics(filters)

        return {"fastest_endpoints": [], "throughput_analysis": []}

    def get_status_code_groups(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.fallback_provider:
            return self.fallback_provider.get_status_code_groups(filters)

        return {"by_endpoint": [], "by_hour": [], "by_day": []}

    def get_extended_visitor_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        upload_id = filters.get("upload_id") if filters else None
        if not upload_id: return {"browser_distribution": [], "os_distribution": []}

        data = self._run_goaccess(upload_id)
        if not data and self.fallback_provider:
            return self.fallback_provider.get_extended_visitor_analytics(filters)

        if not data: return {"browser_distribution": [], "os_distribution": []}

        browsers = data.get("browsers", {}).get("data", [])
        os_data = data.get("os", {}).get("data", [])

        return {
            "browser_distribution": [{"browser": b["data"], "count": b["hits"]["count"]} for b in browsers],
            "os_distribution": [{"os": o["data"], "count": o["hits"]["count"]} for o in os_data]
        }
