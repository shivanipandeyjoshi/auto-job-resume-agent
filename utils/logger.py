from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from utils.config_manager import ConfigManager


class AppLogger:
    """Centralized logger with console and rotating file handlers."""

    def __init__(self, config_manager: ConfigManager | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = logger
        self._configure()

    def _configure(self) -> None:
        log_dir = Path(self.config_manager.get("project.logs_dir", "logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        self.logger.remove()
        self.logger.add(
            sys.stdout,
            level=self.config_manager.get("logging.level", "INFO"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )
        self.logger.add(
            str(log_dir / "app.log"),
            rotation=self.config_manager.get("logging.rotation", "10 MB"),
            retention=self.config_manager.get("logging.retention", "30 days"),
            level=self.config_manager.get("logging.level", "INFO"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )

    def get_logger(self):
        """Return the configured Loguru logger."""

        return self.logger


def resolve_logger(logger: object | None = None, config_manager: ConfigManager | None = None):
    """Return a usable Loguru logger from either an AppLogger wrapper or a raw logger."""

    if logger is None:
        return AppLogger(config_manager).get_logger()
    if isinstance(logger, AppLogger):
        return logger.get_logger()
    if hasattr(logger, "get_logger"):
        return logger.get_logger()
    return logger
