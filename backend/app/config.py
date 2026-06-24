import yaml
import os
from typing import Dict, Any

class Config:
    def __init__(self, config_path: str = "backend/config.yaml"):
        # Try different paths relative to the execution root
        paths_to_try = [config_path, "config.yaml", "../config.yaml"]
        self.config_data = {}

        for path in paths_to_try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.config_data = yaml.safe_load(f)
                break

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

# Singleton instance
config = Config()
