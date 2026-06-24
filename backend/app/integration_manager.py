import os
import subprocess
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime

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
            "sigma": {
                "name": "Sigma",
                "type": "security",
                "version": "1.0.0" # Internal versioning
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
            return False

        binary = info.get("binary")
        if binary:
            return shutil.which(binary) is not None

        # Non-binary tools (like sigma) are checked differently if needed
        return True

    def get_tool_status(self) -> Dict[str, Any]:
        """
        Get the status and version of all registered integrations.
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

            elif key == "sigma":
                # Assuming sigma rules are in a specific directory
                rules_dir = "backend/rules/sigma"
                if os.path.exists(rules_dir):
                    rule_count = len([f for f in os.listdir(rules_dir) if f.endswith(".yml") or f.endswith(".yaml")])
                    tool_status["rule_count"] = rule_count
                else:
                    tool_status["rule_count"] = 0
                tool_status["version"] = info.get("version")
                tool_status["healthy"] = True

            # Add execution metadata if available
            if key in self.execution_metadata:
                tool_status["execution"] = self.execution_metadata[key]

            status[key] = tool_status

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
