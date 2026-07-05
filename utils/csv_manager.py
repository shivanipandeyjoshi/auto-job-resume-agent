from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CsvManager:
    """Write metadata rows to a CSV file."""

    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.csv_path.exists():
            self.csv_path.write_text("", encoding="utf-8")

    def append_row(self, row: dict[str, Any]) -> None:
        """Append a row to the CSV file."""

        file_exists = self.csv_path.exists() and self.csv_path.stat().st_size > 0
        with self.csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
