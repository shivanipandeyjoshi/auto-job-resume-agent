from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class JobSummary(BaseModel):
    """A concise representation of a discovered job posting."""

    title: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    location: str = Field(default="")
    experience: str = Field(default="")
    job_url: str = Field(default="")
    apply_url: str = Field(default="")
    employment_type: str = Field(default="")
    remote_type: str = Field(default="")
    salary: str = Field(default="")
    posting_age: str = Field(default="")
    source: str = Field(default="")


class JobDescription(BaseModel):
    """A detailed description extracted for a job posting."""

    title: str = Field(default="")
    company: str = Field(default="")
    location: str = Field(default="")
    description: str = Field(default="")
    responsibilities: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    employment_type: str = Field(default="")
    experience: str = Field(default="")
    education: str = Field(default="")
    source_url: str = Field(default="")


class ExperienceEntry(BaseModel):
    """A single professional experience entry."""

    role: str = Field(default="")
    company: str = Field(default="")
    duration: str = Field(default="")
    highlights: List[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    """A project entry from the resume."""

    name: str = Field(default="")
    description: str = Field(default="")
    technologies: List[str] = Field(default_factory=list)


class Resume(BaseModel):
    """Structured representation of the master resume."""

    summary: str = Field(default="")
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class OptimizedResume(BaseModel):
    """An ATS-optimized resume payload."""

    summary: str = Field(default="")
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    ats_score: int = Field(default=0)
    notes: List[str] = Field(default_factory=list)


class Metadata(BaseModel):
    """Metadata written to CSV for each generated resume."""

    date: str = Field(default="")
    company: str = Field(default="")
    position: str = Field(default="")
    resume_path: str = Field(default="")
    pdf_path: str = Field(default="")
    job_url: str = Field(default="")
    apply_url: str = Field(default="")
    ranking: float = Field(default=0.0)
    ats_score: int = Field(default=0)
    status: str = Field(default="generated")
    notes: str = Field(default="")


class SearchConfiguration(BaseModel):
    """Configuration for job discovery."""

    keywords: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    portal: str = Field(default="")
    limit: int = Field(default=10)


class ApplicationState(BaseModel):
    """State object passed between LangGraph nodes."""

    job_summaries: List[JobSummary] = Field(default_factory=list)
    job_descriptions: List[JobDescription] = Field(default_factory=list)
    ranked_jobs: List[dict[str, Any]] = Field(default_factory=list)
    resume: Optional[Resume] = None
    optimized_resume: Optional[OptimizedResume] = None
    validation_report: dict[str, Any] = Field(default_factory=dict)
    generated_files: List[str] = Field(default_factory=list)
    metadata: List[Metadata] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
