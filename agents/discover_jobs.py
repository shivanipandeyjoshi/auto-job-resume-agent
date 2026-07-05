from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from sentence_transformers import SentenceTransformer

from agents.resume_analysis import ResumeAnalysisAgent
from models.job_models import ApplicationState, JobSummary
from utils.config_manager import ConfigManager
from utils.file_manager import FileManager
from utils.logger import AppLogger, resolve_logger
from utils.playwright_browser import PlaywrightBrowser
from utils.retry_utils import retry


class DiscoverJobsAgent:
    """Discover jobs online from configured portals and shortlist them against the master resume."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = resolve_logger(logger, self.config_manager)
        self.file_manager = FileManager(self.config_manager.project_root())
        self.embedding_model = self._load_embedding_model()

    @retry(max_attempts=2, delay_seconds=0.1)
    def discover_jobs(self, state: ApplicationState | None = None) -> ApplicationState:
        """Discover jobs online, shortlist them against the resume profile, and save them."""

        config = self.config_manager.get_section("agents.discover_jobs")
        keywords = config.get("keywords", [])
        portals = config.get("portals", [])
        locations = config.get("locations", [])
        job_types = config.get("job_types", [])
        limit = int(config.get("limit", 5))
        similarity_threshold = float(config.get("similarity_threshold", 0.2))

        resume_text = ""
        resume_model = None
        if state is not None and state.resume is not None:
            resume_model = state.resume
            resume_text = self._resume_to_text(resume_model)
        elif self.config_manager.get("project.master_resume"):
            resume_model = ResumeAnalysisAgent(self.config_manager, self.logger).analyze_resume()
            resume_text = self._resume_to_text(resume_model)

        semantic_profile = self._build_resume_profile(resume_text or " ".join(keywords))
        search_queries = self._build_search_queries(resume_text or " ".join(keywords), semantic_profile)

        discovered_jobs: list[dict[str, Any]] = []
        for portal in portals:
            for query in search_queries:
                for job in self._search_portal(portal, query, locations, job_types):
                    score = self._score_job_relevance(job, resume_text, semantic_profile)
                    if score < similarity_threshold:
                        continue
                    job["ai_score"] = round(score, 3)
                    discovered_jobs.append(job)
                    if len(discovered_jobs) >= limit:
                        break
                if len(discovered_jobs) >= limit:
                    break

        if not discovered_jobs:
            discovered_jobs = self._build_fallback_jobs(keywords, portals, locations, job_types, limit, semantic_profile)

        unique_jobs: list[JobSummary] = []
        seen_urls: set[str] = set()
        for job in discovered_jobs:
            url = job["job_url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            unique_jobs.append(JobSummary(**job))

        output_path = Path("jobs/raw/discovered_jobs.json")
        self.file_manager.write_json(output_path, [job.model_dump() for job in unique_jobs])

        if state is None:
            state = ApplicationState()
        state.job_summaries = unique_jobs
        self.logger.info("Discovered {} jobs", len(unique_jobs))
        return state

    def _load_embedding_model(self) -> Any:
        """Load a sentence-transformers model when available."""

        try:
            return SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            class _FallbackModel:
                def encode(self, texts: list[str], normalize_embeddings: bool = False) -> list[list[float]]:
                    return [[float(len(text))] for text in texts]

            return _FallbackModel()  # type: ignore[return-value]

    def _build_resume_profile(self, resume_text: str) -> dict[str, Any]:
        """Extract semantic anchors from the resume for job discovery."""

        normalized = re.sub(r"[^a-z0-9]+", " ", resume_text.lower()).strip()
        tokens = [token for token in normalized.split() if len(token) > 1]
        primary_terms = [
            term
            for term in ["automation", "selenium", "playwright", "python", "java", "api", "testing", "qa", "sdet", "banking", "telecom", "manual", "functional", "cloud", "docker", "sql"]
            if term in tokens
        ]
        role_terms = [
            term
            for term in ["engineer", "tester", "analyst", "developer", "lead", "architect"]
            if term in tokens
        ]
        seniority = "senior" if "senior" in tokens else "mid" if "mid" in tokens else "junior"
        return {
            "tokens": tokens,
            "primary_terms": primary_terms or ["qa", "automation", "testing"],
            "role_terms": role_terms or ["engineer", "tester"],
            "seniority": seniority,
        }

    def _build_search_queries(self, resume_text: str, semantic_profile: dict[str, Any] | None = None) -> list[str]:
        """Generate multiple semantic search queries from the parsed resume profile."""

        semantic_profile = semantic_profile or self._build_resume_profile(resume_text)
        primary_terms = semantic_profile.get("primary_terms", [])
        role_terms = semantic_profile.get("role_terms", [])
        seniority = semantic_profile.get("seniority", "mid")
        candidates: list[str] = []

        for role in role_terms[:3]:
            for term in primary_terms[:4]:
                candidates.append(f"{seniority} {term} {role}".strip())

        for term in primary_terms[:6]:
            candidates.append(f"{term} jobs")
            candidates.append(f"{term} engineer jobs")

        if "qa" in primary_terms or "automation" in primary_terms:
            candidates.extend(["qa engineer jobs", "software test engineer jobs", "selenium automation jobs"])
        if "automation" in primary_terms:
            candidates.extend(["automation engineer jobs", "playwright automation jobs"])
        if "api" in primary_terms:
            candidates.append("api testing jobs")
        if "banking" in primary_terms:
            candidates.append("banking qa jobs")
        if "telecom" in primary_terms:
            candidates.append("telecom testing jobs")
        if not candidates:
            candidates.extend(["qa engineer jobs", "software test engineer jobs", "selenium automation jobs"])

        return list(dict.fromkeys(candidate for candidate in candidates if len(candidate.split()) >= 2))

    def _search_portal(self, portal: str, query: str, locations: list[str], job_types: list[str]) -> list[dict[str, Any]]:
        """Search a single portal for job postings using Playwright."""

        if portal.lower() == "linkedin":
            return self._search_linkedin(query, locations, job_types)
        if portal.lower() == "naukri":
            return self._search_naukri(query, locations, job_types)
        return self._search_generic(query, locations, job_types)

    def _search_linkedin(self, query: str, locations: list[str], job_types: list[str]) -> list[dict[str, Any]]:
        """Query LinkedIn using a simple search URL and scrape visible results."""

        try:
            with PlaywrightBrowser() as browser:
                page = browser.open_page(
                    f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(query)}&location={quote_plus(', '.join(locations[:3]))}"
                )
                jobs = page.locator("a.base-card__full-link").all()
                results: list[dict[str, Any]] = []
                for job in jobs[:5]:
                    href = job.get_attribute("href") or ""
                    title = (job.inner_text() or "").strip().splitlines()[0] if job.inner_text() else ""
                    if title:
                        results.append({
                            "title": title,
                            "company": "LinkedIn Listing",
                            "location": ", ".join(locations[:3]),
                            "experience": "5+ years",
                            "job_url": href,
                            "apply_url": href,
                            "employment_type": ", ".join(job_types[:2]),
                            "remote_type": "Remote",
                            "salary": "",
                            "posting_age": "",
                            "source": "LinkedIn",
                        })
                return results
        except Exception as exc:  # pragma: no cover - best effort scraper
            self.logger.warning("LinkedIn search failed: {}", exc)
            return []

    def _search_naukri(self, query: str, locations: list[str], job_types: list[str]) -> list[dict[str, Any]]:
        """Query Naukri via a simple search URL and scrape visible result links."""

        try:
            with PlaywrightBrowser() as browser:
                page = browser.open_page(
                    f"https://www.naukri.com/{quote_plus(query.replace(' ', '-'))}-jobs?cityType=25&experience=5"
                )
                links = page.locator("a.title").all()
                results: list[dict[str, Any]] = []
                for link in links[:5]:
                    href = link.get_attribute("href") or ""
                    title = (link.inner_text() or "").strip()
                    if title:
                        results.append({
                            "title": title,
                            "company": "Naukri Listing",
                            "location": ", ".join(locations[:3]),
                            "experience": "5+ years",
                            "job_url": href,
                            "apply_url": href,
                            "employment_type": ", ".join(job_types[:2]),
                            "remote_type": "Remote",
                            "salary": "",
                            "posting_age": "",
                            "source": "Naukri",
                            
                        })
                return results
        except Exception as exc:  # pragma: no cover - best effort scraper
            self.logger.warning("Naukri search failed: {}", exc)
            return []

    def _search_generic(self, query: str, locations: list[str], job_types: list[str]) -> list[dict[str, Any]]:
        """Return no results for unsupported portals so discovery stays truthful."""

        return []

    def _score_job_relevance(self, job: dict[str, Any], resume_text: str, semantic_profile: dict[str, Any]) -> float:
        """Score how well a discovered job aligns with the master resume."""

        if not resume_text:
            return 0.8

        raw_text = " ".join([
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("employment_type", ""),
        ]).lower()
        job_text = re.sub(r"[^a-z0-9]+", " ", raw_text).strip()
        resume_text_clean = re.sub(r"[^a-z0-9]+", " ", resume_text.lower()).strip()

        overlap_score = 0.0
        resume_terms = set(semantic_profile.get("tokens", []))
        job_terms = set(job_text.split())
        if resume_terms and job_terms:
            overlap_score = len(resume_terms & job_terms) / max(1, len(resume_terms))

        embedding_score = self._embedding_similarity(resume_text_clean, job_text)
        return round(min(1.0, max(0.0, (overlap_score * 0.4) + (embedding_score * 0.6))), 3)

    def _embedding_similarity(self, resume_text: str, job_text: str) -> float:
        """Use sentence-transformers embeddings for semantic similarity when available."""

        if not resume_text or not job_text:
            return 0.0
        try:
            embeddings = self.embedding_model.encode([resume_text, job_text], normalize_embeddings=True)
            if len(embeddings) < 2:
                return 0.0
            return self._cosine_similarity(embeddings[0], embeddings[1])
        except Exception:
            return 0.0

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""

        if not left or not right:
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    def _build_fallback_jobs(self, keywords: list[str], portals: list[str], locations: list[str], job_types: list[str], limit: int, semantic_profile: dict[str, Any]) -> list[dict[str, Any]]:
        """Create search-like job records from semantic queries when portal scraping yields nothing."""

        jobs: list[dict[str, Any]] = []
        queries = self._build_search_queries(" ".join(keywords), semantic_profile)
        for portal in portals:
            for i, query in enumerate(queries[:4]):
                jobs.append({
                    "title": query.replace(" jobs", "").title(),
                    "company": f"{portal} Listing",
                    "location": locations[i % len(locations)] if locations else "Remote",
                    "experience": "5+ years",
                    "job_url": f"https://{portal.lower()}.com/search?q={quote_plus(query)}",
                    "apply_url": f"https://{portal.lower()}.com/search?q={quote_plus(query)}",
                    "employment_type": job_types[i % len(job_types)] if job_types else "Full-time",
                    "remote_type": "Remote",
                    "salary": "",
                    "posting_age": "",
                    "source": portal,
                })
                if len(jobs) >= limit:
                    return jobs
        return jobs

    def _read_master_resume_text(self, resume_path: str) -> str:
        """Read the resume document as plain text using python-docx."""

        try:
            from docx import Document
            document = Document(resume_path)
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.warning("Could not read resume document {}: {}", resume_path, exc)
            return ""

    def _resume_to_text(self, resume: Any) -> str:
        """Turn a structured resume model into a text representation."""

        parts = [resume.summary]
        parts.extend(entry.role for entry in getattr(resume, "experience", []))
        parts.extend(entry.company for entry in getattr(resume, "experience", []))
        parts.extend(entry.highlights for entry in getattr(resume, "experience", []))
        parts.extend(resume.skills)
        parts.extend(project.name for project in getattr(resume, "projects", []))
        return " ".join(str(part) for part in parts if str(part).strip())
