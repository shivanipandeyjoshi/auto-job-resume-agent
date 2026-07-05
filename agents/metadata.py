from __future__ import annotations

from pathlib import Path

from models.job_models import ApplicationState, Metadata
from utils.config_manager import ConfigManager
from utils.csv_manager import CsvManager
from utils.logger import AppLogger, resolve_logger


class MetadataAgent:
    """Append resume generation metadata to the CSV history."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = resolve_logger(logger, self.config_manager)

    def write_metadata(self, state: ApplicationState) -> ApplicationState:
        """Persist metadata rows for generated resumes."""

        csv_path = Path(self.config_manager.get("project.csv_dir", "csv")) / "resume_history.csv"
        manager = CsvManager(csv_path)
        for record in state.metadata:
            manager.append_row(record.model_dump())
        self.logger.info("Wrote {} metadata rows", len(state.metadata))
        return state
