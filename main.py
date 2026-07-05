from __future__ import annotations

import argparse

from agents.workflow import ResumeWorkflow
from models.job_models import ApplicationState
from utils.config_manager import ConfigManager


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the local CLI."""

    parser = argparse.ArgumentParser(description="Local AI job resume agent")
    parser.add_argument("--discover", action="store_true", help="Run job discovery only")
    parser.add_argument("--extract", action="store_true", help="Run extraction only")
    parser.add_argument("--optimize", action="store_true", help="Run optimization only")
    parser.add_argument("--generate", action="store_true", help="Run full generation")
    parser.add_argument("--all", action="store_true", help="Run the complete workflow")
    return parser.parse_args()


def main() -> None:
    """Run the selected workflow step or the full workflow."""

    args = parse_args()
    config = ConfigManager()
    workflow = ResumeWorkflow(config)

    if args.all or not any([args.discover, args.extract, args.optimize, args.generate]):
        workflow.run(ApplicationState())
        return

    state = ApplicationState()
    if args.discover:
        from agents.discover_jobs import DiscoverJobsAgent
        state = DiscoverJobsAgent(config).discover_jobs(state)
    if args.extract:
        from agents.extract_job import ExtractJobAgent
        state = ExtractJobAgent(config).extract(state)
    if args.optimize:
        from agents.resume_analysis import ResumeAnalysisAgent
        from agents.optimize_resume import OptimizeResumeAgent
        resume = ResumeAnalysisAgent(config).analyze_resume()
        state.resume = resume
        state = OptimizeResumeAgent(config).optimize(state, resume)
    if args.generate:
        from agents.generate_resume import GenerateResumeAgent
        state = GenerateResumeAgent(config).generate(state)


if __name__ == "__main__":
    main()
