from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileManager:
    """Simple file-system helpers for the application."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.root_dir = Path(root_dir or ".").resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def ensure_dir(self, path: str | Path) -> Path:
        """Create a directory and return its path."""

        directory = self.root_dir / path if not Path(path).is_absolute() else Path(path)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def write_json(self, path: str | Path, data: Any) -> Path:
        """Write JSON data to disk."""

        file_path = self.root_dir / path if not Path(path).is_absolute() else Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        return file_path

    def read_json(self, path: str | Path) -> Any:
        """Read JSON data from disk."""

        file_path = self.root_dir / path if not Path(path).is_absolute() else Path(path)
        if not file_path.exists():
            return None
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
