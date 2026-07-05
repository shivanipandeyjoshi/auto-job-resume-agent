from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, StateGraph

from agents.discover_jobs import DiscoverJobsAgent
from agents.extract_job import ExtractJobAgent
from agents.generate_resume import GenerateResumeAgent
from agents.metadata import MetadataAgent
from agents.optimize_resume import OptimizeResumeAgent
from agents.ranking import RankingAgent
from agents.resume_analysis import ResumeAnalysisAgent
from agents.validate_resume import ValidateResumeAgent
from models.job_models import ApplicationState
from utils.config_manager import ConfigManager
from utils.logger import AppLogger, resolve_logger


class ResumeWorkflow:
    """Compose the local resume generation workflow as a LangGraph graph."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = resolve_logger(logger, self.config_manager)
        self.discover_agent = DiscoverJobsAgent(self.config_manager, logger)
        self.extract_agent = ExtractJobAgent(self.config_manager, logger)
        self.ranking_agent = RankingAgent(self.config_manager, logger)
        self.analysis_agent = ResumeAnalysisAgent(self.config_manager, logger)
        self.optimize_agent = OptimizeResumeAgent(self.config_manager, logger)
        self.validate_agent = ValidateResumeAgent(self.config_manager, logger)
        self.generate_agent = GenerateResumeAgent(self.config_manager, logger)
        self.metadata_agent = MetadataAgent(self.config_manager, logger)

    def build_graph(self) -> StateGraph:
        """Build the workflow graph with one node per agent."""

        workflow = StateGraph(ApplicationState)
        workflow.add_node("discover_jobs", self._discover_jobs)
        workflow.add_node("extract_jobs", self._extract_jobs)
        workflow.add_node("rank_jobs", self._rank_jobs)
        workflow.add_node("analyze_resume", self._analyze_resume)
        workflow.add_node("optimize_resume", self._optimize_resume)
        workflow.add_node("validate_resume", self._validate_resume)
        workflow.add_node("generate_resume", self._generate_resume)
        workflow.add_node("write_metadata", self._write_metadata)

        workflow.set_entry_point("discover_jobs")
        workflow.add_edge("discover_jobs", "extract_jobs")
        workflow.add_edge("extract_jobs", "rank_jobs")
        workflow.add_edge("rank_jobs", "analyze_resume")
        workflow.add_edge("analyze_resume", "optimize_resume")
        workflow.add_edge("optimize_resume", "validate_resume")
        workflow.add_edge("validate_resume", "generate_resume")
        workflow.add_edge("generate_resume", "write_metadata")
        workflow.add_edge("write_metadata", END)
        return workflow.compile()

    def run(self, state: ApplicationState | None = None) -> ApplicationState:
        """Execute the workflow and return the final state."""

        initial_state = state or ApplicationState()
        app = self.build_graph()
        return app.invoke(initial_state)

    def _discover_jobs(self, state: ApplicationState) -> ApplicationState:
        return self.discover_agent.discover_jobs(state)

    def _extract_jobs(self, state: ApplicationState) -> ApplicationState:
        return self.extract_agent.extract(state)

    def _rank_jobs(self, state: ApplicationState) -> ApplicationState:
        if state.resume is None:
            state.resume = self.analysis_agent.analyze_resume()
        return self.ranking_agent.rank(state, state.resume)

    def _analyze_resume(self, state: ApplicationState) -> ApplicationState:
        state.resume = self.analysis_agent.analyze_resume()
        return state

    def _optimize_resume(self, state: ApplicationState) -> ApplicationState:
        if state.resume is None:
            state.resume = self.analysis_agent.analyze_resume()
        return self.optimize_agent.optimize(state, state.resume)

    def _validate_resume(self, state: ApplicationState) -> ApplicationState:
        return self.validate_agent.validate(state)

    def _generate_resume(self, state: ApplicationState) -> ApplicationState:
        return self.generate_agent.generate(state)

    def _write_metadata(self, state: ApplicationState) -> ApplicationState:
        return self.metadata_agent.write_metadata(state)
