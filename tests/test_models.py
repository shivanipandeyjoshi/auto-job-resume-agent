from models.job_models import ApplicationState, JobSummary, Resume


def test_job_summary_model():
    job = JobSummary(
        title="Python Engineer",
        company="Example",
        location="Remote",
        experience="3+ years",
        job_url="https://example.com/job",
        apply_url="https://example.com/apply",
        employment_type="Full-time",
        remote_type="Remote",
        salary="$120k",
        posting_age="2d",
        source="LinkedIn",
    )
    assert job.title == "Python Engineer"
    assert job.company == "Example"


def test_resume_model():
    resume = Resume(
        summary="Experienced engineer",
        experience=[],
        projects=[],
        skills=["Python"],
        education=[],
        certifications=[],
        achievements=[],
    )
    assert resume.summary == "Experienced engineer"


def test_application_state_defaults():
    state = ApplicationState()
    assert state.job_summaries == []
    assert state.job_descriptions == []
