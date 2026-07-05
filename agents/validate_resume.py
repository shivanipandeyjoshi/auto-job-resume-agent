from __future__ import annotations

from models.job_models import ApplicationState, OptimizedResume
from utils.ats_scorer import AtsScorer
from utils.config_manager import ConfigManager
from utils.logger import AppLogger, resolve_logger


class ValidateResumeAgent:
    """Validate the optimized resume against ATS and consistency rules."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = resolve_logger(logger, self.config_manager)
        self.ats_scorer = AtsScorer()

    def validate(self, state: ApplicationState) -> ApplicationState:
        """Return a validation report with issues and a final ATS score."""

        resume = state.optimized_resume or OptimizedResume()
        keywords = self.config_manager.get("resume.ats_keywords", [])
        score = self.ats_scorer.score(" ".join(resume.skills + [resume.summary]), keywords)
        issues: list[str] = []
        if not resume.summary:
            issues.append("Summary is missing")
        if not resume.skills:
            issues.append("Skills are missing")
        if score < 70:
            issues.append("ATS keyword coverage is low")

        state.validation_report = {
            "ats_score": score,
            "issues": issues,
            "pages": 1,
            "valid": not issues,
        }
        self.logger.info("Validation report generated with ATS score {}", score)
        return state
