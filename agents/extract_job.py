from __future__ import annotations

from agents.resume_analysis import ResumeAnalysisAgent
from models.job_models import ApplicationState, JobDescription, JobSummary
from utils.config_manager import ConfigManager
from utils.file_manager import FileManager
from utils.logger import AppLogger, resolve_logger


class ExtractJobAgent:
    """Create detailed job descriptions from discovered summaries."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = resolve_logger(logger, self.config_manager)
        self.file_manager = FileManager(self.config_manager.project_root())

    def extract(self, state: ApplicationState) -> ApplicationState:
        """Generate detailed job descriptions for each discovered job summary."""

        resume = ResumeAnalysisAgent(self.config_manager, self.logger).analyze_resume()
        skill_keywords = resume.skills[:8]
        descriptions: list[JobDescription] = []
        for job in state.job_summaries:
            title_tokens = [token for token in job.title.lower().split() if token not in {"and", "for", "the", "with", "a"}]
            focused_skills = [skill for skill in skill_keywords if skill.lower() in job.title.lower() or any(token in skill.lower() for token in title_tokens)]
            if not focused_skills:
                focused_skills = skill_keywords[:5]
            description = JobDescription(
                title=job.title,
                company=job.company,
                location=job.location,
                description=(
                    f"We are looking for a {job.title} who can contribute using {', '.join(focused_skills[:4])} and domain experience from the candidate's background."
                ),
                responsibilities=[
                    "Validate requirements and ensure quality across releases",
                    "Create and execute test plans, cases, and reports",
                    "Work with cross-functional teams to resolve defects and improve reliability",
                ],
                qualifications=["Strong experience in testing and quality engineering", "Familiarity with regression, API, and release validation"],
                skills=focused_skills,
                preferred_skills=["Selenium", "Python", "API Testing", "Automation"],
                benefits=["Remote work", "Health insurance"],
                employment_type=job.employment_type,
                experience=job.experience,
                education="Bachelor's degree or equivalent",
                source_url=job.job_url,
            )
            descriptions.append(description)

        self.file_manager.write_json("jobs/raw/extracted_jobs.json", [item.model_dump() for item in descriptions])
        state.job_descriptions = descriptions
        self.logger.info("Extracted {} job descriptions", len(descriptions))
        return state
