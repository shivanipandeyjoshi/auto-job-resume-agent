from __future__ import annotations

from models.job_models import ApplicationState, Resume
from utils.chroma_store import ChromaStore
from utils.config_manager import ConfigManager
from utils.logger import AppLogger, resolve_logger


class RankingAgent:
    """Rank jobs using semantic similarity based on embeddings."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = resolve_logger(logger, self.config_manager)
        self.store = ChromaStore()

    def rank(self, state: ApplicationState, resume: Resume | None = None) -> ApplicationState:
        """Rank jobs according to resume and job description relevance."""

        if resume is None:
            return state

        resume_text = " ".join([resume.summary, *resume.skills, *[project.name for project in resume.projects]])
        threshold = float(self.config_manager.get("agents.ranking.threshold", 0.35))
        documents = [
            {
                "id": f"job-{index}",
                "text": f"{description.title} {description.description} {' '.join(description.skills)}",
                "metadata": {"title": description.title, "company": description.company},
            }
            for index, description in enumerate(state.job_descriptions)
        ]
        if not documents:
            state.ranked_jobs = []
            self.logger.info("Ranked 0 jobs")
            return state
        self.store.add_documents(documents)
        query_results = self.store.query(resume_text, n_results=max(1, len(documents)))

        ranked: list[dict[str, object]] = []
        resume_terms = [term.lower() for term in resume.skills + [resume.summary] if term]
        for result in query_results:
            metadata = result.get("metadata", {})
            score = max(0.0, 1.0 - float(result.get("distance", 0.0)))
            try:
                job_index = int(result["id"].split("-")[-1])
                job = state.job_descriptions[job_index]
            except (ValueError, IndexError):
                continue
            text = f"{job.title} {job.description} {' '.join(job.skills)}".lower()
            keyword_score = sum(1 for term in resume_terms if term.lower() in text and len(term) > 2)
            adjusted_score = min(1.0, score + (keyword_score * 0.08))
            if adjusted_score >= threshold:
                ranked.append({
                    "job": job,
                    "score": round(adjusted_score, 3),
                })

        if not ranked and state.job_descriptions:
            for index, description in enumerate(state.job_descriptions):
                text = f"{description.title} {description.description} {' '.join(description.skills)}".lower()
                keyword_score = sum(1 for term in resume_terms if term.lower() in text and len(term) > 2)
                if keyword_score:
                    ranked.append({
                        "job": description,
                        "score": round(min(0.95, 0.4 + keyword_score * 0.08), 3),
                    })

        ranked.sort(key=lambda item: item["score"], reverse=True)
        state.ranked_jobs = ranked
        self.logger.info("Ranked {} jobs", len(ranked))
        return state
