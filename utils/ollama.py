from __future__ import annotations

import json
from typing import Any

import requests

from utils.config_manager import ConfigManager
from utils.logger import AppLogger
from utils.retry_utils import retry


class OllamaClient:
    """A small local Ollama client wrapper with retry and health checks."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = (logger or AppLogger(self.config_manager)).get_logger()
        self.base_url = self.config_manager.get("ollama.base_url", "http://127.0.0.1:11434")
        self.timeout = int(self.config_manager.get("ollama.timeout", 60000))
        self.retries = int(self.config_manager.get("ollama.retries", 2))

    @retry(max_attempts=2, delay_seconds=0.1)
    def health_check(self) -> bool:
        """Check whether the Ollama endpoint is responsive."""

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @retry(max_attempts=2, delay_seconds=0.1)
    def generate(self, prompt: str, model: str | None = None) -> dict[str, Any]:
        """Send a generation request to Ollama and return parsed JSON when possible."""

        payload = {
            "model": model or self.config_manager.get("agents.optimize_resume.model", "qwen3:32b"),
            "prompt": prompt,
            "stream": False,
        }
        response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
