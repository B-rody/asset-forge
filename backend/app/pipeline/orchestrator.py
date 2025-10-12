"""
Pipeline Orchestrator
Coordinates the execution of all pipeline agents using OpenAI
"""

import asyncio
from datetime import datetime
from functools import partial
from typing import Dict, Any, Callable
from pathlib import Path

from app.logger import setup_logger
from app.settings import settings
from app.database import DatabaseManager, BundleQueries
from app.pipeline.agents.researcher import ResearcherAgent
from app.pipeline.agents.planner import PlannerAgent
from app.pipeline.agents.maker import MakerAgent
# from app.pipeline.agents.packager import PackagerAgent

logger = setup_logger(__name__)


class PipelineOrchestrator:
    """Orchestrates the execution of all pipeline steps with real OpenAI integration"""

    def __init__(self):
        # Initialize database
        self.db_manager = DatabaseManager(settings.db_path)
        self.bundle_queries = BundleQueries(self.db_manager)

        # Initialize agents with database access
        self.researcher = ResearcherAgent(db_manager=self.db_manager)
        self.planner = PlannerAgent(db_manager=self.db_manager)
        self.maker = MakerAgent(db_manager=self.db_manager)
        #self.packager = PackagerAgent(db_manager=self.db_manager)

    async def run_pipeline(
        self,
        mode: str,
        params: Dict[str, Any],
        emit: Callable[[Dict[str, Any]], None]
    ):
        """
        Run the full pipeline (or research-only mode)

        Args:
            mode: "one_click", "focused", "research_only", or "research_only_focused"
            params: Parameters from frontend (model, keyword, etc.)
            emit: Callback to send events to frontend
        """
        logger.info(f"Starting pipeline in {mode} mode")
        emit({"event": "log", "step": "Orchestrator", "message": f"Starting {mode} pipeline..."})

        # Determine if this is research-only mode
        research_only = mode in ["research_only", "research_only_focused"]

        try:
            # Step 1: Run researcher
            emit({"event": "log", "step": "Researcher", "message": "Starting research..."})
            emit({"event": "progress", "step": "Researcher", "pct": 0})

            # Extract params for researcher
            focus = mode in ["focused", "research_only_focused"]
            niches = params.get("keyword", "") if focus else ""

            # Run researcher in thread pool (sync agent in async context)
            loop = asyncio.get_event_loop()
            research_results = await loop.run_in_executor(
                None,
                partial(self.researcher.execute, emit=emit, focus=focus, niches=niches)
            )

            emit({"event": "progress", "step": "Researcher", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Research complete"})

            # If research-only mode, stop here
            if research_only:
                emit({
                    "event": "done",
                    "success": True,
                    "research_only": True,
                    "result": {
                        "ideas_count": len(research_results.get("ideas", [])) if isinstance(research_results, dict) else 0,
                        "research": research_results
                    }
                })
                return

            # TODO: Add planner, maker, packager steps

            # Emit done event
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": "test-bundle",
                    "research": research_results
                }
            })

        except Exception as e:
            # Don't re-log the error here since agents already log it with their step name
            # Just emit error event and done status

            # Emit error event with step name for log display
            emit({"event": "error", "step": "Researcher", "message": str(e)})

            # Emit done event with failure status (don't re-raise)
            emit({
                "event": "done",
                "success": False,
                "error": str(e)
            })

    async def run_from_idea(
        self,
        idea_id: str,
        emit: Callable[[Dict[str, Any]], None]
    ):
        """
        Run pipeline starting from Planner with an existing idea
        Skips Researcher and goes directly to Planner → Maker → Packager

        Args:
            idea_id: ID of the idea to build bundle from
            emit: Callback to send events to frontend
        """
        logger.info(f"Starting pipeline from idea: {idea_id}")
        emit({"event": "log", "step": "Orchestrator", "message": f"Building bundle from idea {idea_id}..."})

        try:
            # Step 1: Run planner with idea_id
            emit({"event": "log", "step": "Planner", "message": "Designing bundle..."})
            emit({"event": "progress", "step": "Planner", "pct": 0})

            # Run planner in thread pool (sync agent in async context)
            loop = asyncio.get_event_loop()
            planner_result = await loop.run_in_executor(
                None,
                partial(self.planner.execute, idea=idea_id, emit=emit)
            )

            emit({"event": "progress", "step": "Planner", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Bundle planning complete"})

            # TODO: Add maker, packager steps when ready

            # Emit done event
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": planner_result.get("bundle_id", "unknown"),
                    "idea_id": idea_id,
                    "planner": planner_result
                }
            })

        except Exception as e:
            # Don't re-log the error here since agents already log it with their step name
            # Just emit error event and done status

            # Emit error event with step name for log display
            emit({"event": "error", "step": "Planner", "message": str(e)})

            # Emit done event with failure status (don't re-raise)
            emit({
                "event": "done",
                "success": False,
                "error": str(e)
            })

    async def run_maker_from_bundle(
        self,
        bundle_id: str,
        emit: Callable[[Dict[str, Any]], None]
    ):
        """
        Run just the Maker step for an existing bundle
        Assumes bundle has completed planner step and has planner_output

        Args:
            bundle_id: ID of the bundle to generate assets for
            emit: Callback to send events to frontend
        """
        logger.info(f"Starting Maker for bundle: {bundle_id}")
        emit({"event": "log", "step": "Orchestrator", "message": f"Generating assets for bundle {bundle_id}..."})

        try:
            # Validate bundle exists and has planner output
            bundle_record = self.bundle_queries.get_by_id(bundle_id)
            if not bundle_record:
                raise ValueError(f"Bundle not found: {bundle_id}")

            if not bundle_record.planner_output:
                raise ValueError(f"Bundle {bundle_id} has no planner output. Run planner first.")

            # Step 1: Run maker with bundle_id
            emit({"event": "log", "step": "Maker", "message": "Generating assets..."})
            emit({"event": "progress", "step": "Maker", "pct": 0})

            # Run maker in thread pool (sync agent in async context)
            loop = asyncio.get_event_loop()
            maker_result = await loop.run_in_executor(
                None,
                partial(self.maker.execute, bundle_id=bundle_id, emit=emit)
            )

            emit({"event": "progress", "step": "Maker", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Asset generation complete"})

            # TODO: Add packager step when ready

            # Emit done event
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": bundle_id,
                    "status": "Assets generated successfully"
                }
            })

        except Exception as e:
            # Don't re-log the error here since agents already log it with their step name
            # Just emit error event and done status

            # Emit error event with step name for log display
            emit({"event": "error", "step": "Maker", "message": str(e)})

            # Emit done event with failure status (don't re-raise)
            emit({
                "event": "done",
                "success": False,
                "error": str(e)
            })