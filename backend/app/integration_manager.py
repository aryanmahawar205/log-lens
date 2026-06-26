import os
import subprocess
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.config import config

class IntegrationManager:
    """
    Manages external tool integrations and their lifecycle.
    """

    def __init__(self):
        self.integrations = {
            "goaccess": {
                "name": "GoAccess",
                "type": "analytics",
                "binary": "goaccess"
            },
            "duckdb": {
                "name": "DuckDB",
                "type": "storage"
            }
        }
        self.reload_timestamps = {}
        self.execution_metadata = {}

    def record_execution(self, tool_key: str, status: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Record execution metrics for a tool."""
        self.execution_metadata[tool_key] = {
            "last_status": status,
            "last_execution": datetime.now().isoformat(),
            "duration": duration,
            "metadata": metadata or {}
        }

    def is_tool_available(self, tool_key: str) -> bool:
        """Check if a tool is installed and available."""
        info = self.integrations.get(tool_key)
        if not info:
            # Fallback for dynamic providers
            return True

        binary = info.get("binary")
        if binary:
            return shutil.which(binary) is not None

        return True

    def get_tool_status(self) -> Dict[str, Any]:
        """
        Get the status and version of all registered integrations.
        Includes dynamic status from Security DetectionManager.
        """
        status = {}
        for key, info in self.integrations.items():
            tool_status = {
                "enabled": True,
                "name": info["name"],
                "type": info["type"],
                "last_reload": self.reload_timestamps.get(key),
                "healthy": True
            }

            if key == "goaccess":
                try:
                    if shutil.which("goaccess"):
                        version_out = subprocess.check_output(["goaccess", "--version"]).decode().split("\n")[0]
                        tool_status["version"] = version_out.replace("GoAccess - ", "")
                        tool_status["healthy"] = True
                    else:
                        tool_status["version"] = "Not Installed"
                        tool_status["healthy"] = False
                        tool_status["enabled"] = False
                except Exception:
                    tool_status["version"] = "Error"
                    tool_status["healthy"] = False
                    tool_status["enabled"] = False

            elif key == "duckdb":
                try:
                    import duckdb
                    tool_status["version"] = duckdb.__version__
                    tool_status["healthy"] = True
                except ImportError:
                    tool_status["version"] = "Not Installed"
                    tool_status["healthy"] = False
                    tool_status["enabled"] = False

            # Add execution metadata if available
            if key in self.execution_metadata:
                tool_status["execution"] = self.execution_metadata[key]

            status[key] = tool_status

        # Dynamically fetch Detection Providers
        try:
            # Import here to avoid circular imports during startup
            from app.api.routes.security import security_analyzer
            if security_analyzer and hasattr(security_analyzer, 'sigma_engine'):
                sigma_diag = security_analyzer.sigma_engine.get_diagnostics()
                status['sigma'] = {
                    "enabled": sigma_diag.get("enabled", False),
                    "healthy": sigma_diag.get("healthy_state", False),
                    "provider": "SigmaEngine",
                    "version": sigma_diag.get("version"),
                    "rule_count": sigma_diag.get("loaded_rules"),
                    "loaded_rules": sigma_diag.get("loaded_rules"),
                    "failed_rules": sigma_diag.get("failed_rules"),
                    "ignored_rules": sigma_diag.get("ignored_rules", 0),
                    "last_reload": sigma_diag.get("last_reload"),
                    "last_execution": sigma_diag.get("last_execution_timestamp"),
                    "processing_time_ms": sigma_diag.get("execution_duration", 0) * 1000 if sigma_diag.get("execution_duration") else 0
                }
        except Exception as e:
            print(f"Error fetching detection provider status: {e}")

        return status

    def record_reload(self, tool_key: str):
        self.reload_timestamps[tool_key] = datetime.now().isoformat()

    def register_integration(self, key: str, name: str, tool_type: str, binary: Optional[str] = None):
        """Register a new integration at runtime."""
        self.integrations[key] = {
            "name": name,
            "type": tool_type,
            "binary": binary
        }

# Global instance
integration_manager = IntegrationManager()
