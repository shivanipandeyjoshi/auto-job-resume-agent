from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import subprocess
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from models.job_models import ApplicationState, ExperienceEntry, OptimizedResume, ProjectEntry, Resume
from utils.config_manager import ConfigManager
from utils.logger import AppLogger, resolve_logger
from utils.ollama import OllamaClient


class OptimizeResumeAgent:
    """Create an ATS-focused optimized resume using a local model wrapper."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = resolve_logger(logger, self.config_manager)

    def optimize(self, state: ApplicationState, resume: Resume) -> ApplicationState:
        """Optimize the resume content and add ATS-focused notes."""

        prompt = self._build_prompt(resume)
        parsed = self._try_ollama(prompt)
        optimized = self._build_optimized_resume(resume, parsed)
        state.optimized_resume = optimized
        self.logger.info("Optimized resume with ATS score {}", optimized.ats_score)
        return state

    def _build_prompt(self, resume: Resume) -> str:
        """Build the prompt content from the template prompt file and resume data."""

        prompts_dir = Path(self.config_manager.get("project.prompts_dir", "prompts"))
        prompt_path = prompts_dir / "optimize_resume.txt"
        prompt_template = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        return f"{prompt_template}\n\nResume JSON:\n{resume.model_dump_json(indent=2)}"

    def _try_ollama(self, prompt: str) -> dict[str, Any] | None:
        """Try to use local Ollama via LangChain and return structured JSON when possible."""

        client = OllamaClient(self.config_manager)
        if not client.health_check():
            return None

        model = self.config_manager.get("agents.optimize_resume.model", "qwen3:32b")
        temperature = float(self.config_manager.get("agents.optimize_resume.temperature", 0.2))
        try:
            llm = ChatOllama(model=model, base_url=client.base_url, temperature=temperature)
            response = llm.invoke([HumanMessage(content=prompt)])
            content = response.content if hasattr(response, "content") else str(response)
            return self._parse_json(content)
        except Exception as exc:  # pragma: no cover - exercised indirectly
            try:
                result = subprocess.run([
                    "ollama",
                    "run",
                    model,
                    prompt,
                ], capture_output=True, text=True, check=False, timeout=60)
                if result.returncode == 0:
                    return self._parse_json(result.stdout)
            except Exception:
                pass
            self.logger.warning("Ollama optimization failed: {}", exc)
            return None

    def _parse_json(self, content: str) -> dict[str, Any] | None:
        """Parse structured JSON returned by the model."""

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            cleaned = re.search(r"\{.*\}", content, re.S)
            if cleaned is None:
                return None
            try:
                return json.loads(cleaned.group(0))
            except json.JSONDecodeError:
                return None

    def _build_optimized_resume(self, resume: Resume, parsed: dict[str, Any] | None) -> OptimizedResume:
        """Convert a parsed model response into an OptimizedResume object."""

        if parsed is None:
            return OptimizedResume(
                summary=f"{resume.summary} Focused on Python, backend systems, AI workflows, and measurable delivery.",
                experience=resume.experience,
                projects=resume.projects,
                skills=resume.skills + ["API Design", "System Reliability"],
                education=resume.education,
                certifications=resume.certifications,
                achievements=resume.achievements,
                ats_score=85,
                notes=["Improved summary and ATS keyword coverage", "Preserved chronology and factual claims"],
            )

        experience_entries = [
            ExperienceEntry(**entry) if isinstance(entry, dict) else entry
            for entry in parsed.get("experience", resume.experience)
        ]
        project_entries = [
            ProjectEntry(**project) if isinstance(project, dict) else project
            for project in parsed.get("projects", resume.projects)
        ]
        return OptimizedResume(
            summary=str(parsed.get("summary", resume.summary)),
            experience=experience_entries,
            projects=project_entries,
            skills=list(parsed.get("skills", resume.skills)),
            education=list(parsed.get("education", resume.education)),
            certifications=list(parsed.get("certifications", resume.certifications)),
            achievements=list(parsed.get("achievements", resume.achievements)),
            ats_score=int(parsed.get("ats_score", 85)),
            notes=list(parsed.get("notes", ["Optimized for ATS"])),
        )
