import os
import subprocess
from typing import Dict, Any, Optional
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

    def get_tool_status(self) -> Dict[str, Any]:
        """
        Get the status and version of all registered integrations.
        """
        status = {}
        for key, info in self.integrations.items():
            tool_status = {
                "enabled": True, # For now, all are considered enabled if they can be found
                "name": info["name"],
                "type": info["type"],
                "last_reload": self.reload_timestamps.get(key)
            }

            if key == "goaccess":
                try:
                    version_out = subprocess.check_output(["goaccess", "--version"]).decode().split("\n")[0]
                    tool_status["version"] = version_out.replace("GoAccess - ", "")
                    tool_status["healthy"] = True
                except Exception:
                    tool_status["version"] = "Not Installed"
                    tool_status["healthy"] = False
                    tool_status["enabled"] = False

            elif key == "duckdb":
                import duckdb
                tool_status["version"] = duckdb.__version__
                tool_status["healthy"] = True

            elif key == "sigma":
                # Assuming sigma rules are in a specific directory
                rules_dir = "backend/rules/sigma"
                if os.path.exists(rules_dir):
                    rule_count = len([f for f in os.listdir(rules_dir) if f.endswith(".yml") or f.endswith(".yaml")])
                    tool_status["rule_count"] = rule_count
                tool_status["version"] = info.get("version")
                tool_status["healthy"] = True

            status[key] = tool_status

        return status

    def record_reload(self, tool_key: str):
        self.reload_timestamps[tool_key] = datetime.now().isoformat()

# Global instance
integration_manager = IntegrationManager()
