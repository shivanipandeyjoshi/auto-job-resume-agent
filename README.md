# Auto Job Resume Agent

An intelligent local workflow that reads a master resume, discovers relevant jobs, ranks them against the resume profile, tailors the resume content, and generates a polished DOCX/PDF output.

## Features

- Reads the master resume from DOCX
- Extracts structured resume data such as summary, skills, experience, projects, certifications, and achievements
- Builds resume-aware search queries for job discovery
- Scores discovered jobs against the resume using semantic similarity and keyword overlap
- Generates tailored resume artifacts in DOCX/PDF format
- Stores job and generation metadata for traceability

## Requirements

- Python 3.10+
- Ollama installed locally
- Optional: Playwright for portal-based browsing

## Setup

1. Create and activate a virtual environment
2. Install dependencies
3. Configure the resume path and local model in config/config.yaml
4. Run the workflow:

```bash
source .venv/bin/activate
python3 main.py --all
```

## Project Structure

- agents/: workflow and agent implementations
- config/: YAML configuration
- jobs/: discovered and extracted job data
- models/: Pydantic models
- resumes/: generated outputs and master resume
- tests/: regression tests
- utils/: helper modules

## Notes

The workflow is designed to run locally and uses a local Ollama model for resume optimization.
