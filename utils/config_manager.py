from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigManager:
    """Loads and exposes project configuration from YAML."""

    def __init__(self, config_path: str | None = None) -> None:
        self.config_path = Path(config_path or "config/config.yaml")
        self._config = self._load()

    def _load(self) -> dict[str, Any]:
        with self.config_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Return a nested configuration value using dot notation."""

        value: Any = self._config
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def get_section(self, section: str) -> dict[str, Any]:
        """Return a configuration section as a dictionary."""

        return self.get(section, {}) or {}

    def project_root(self) -> Path:
        """Return the project root directory."""

        return Path(self.get("project.root_dir", ".")).resolve()
