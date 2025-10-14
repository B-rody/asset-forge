"""
Pipeline Orchestrator
Coordinates the execution of all pipeline agents using OpenAI
"""

import asyncio
import json
from datetime import datetime
from functools import partial
from typing import Dict, Any, Callable
from pathlib import Path
from uuid import uuid4

from app.logger import setup_logger
from app.settings import settings
from app.database import DatabaseManager, BundleQueries
from app.database.queries import ActivityLogQueries, CreatedBundleQueries
from app.database.models import ActivityLog, CreatedBundle
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
        self.activity_queries = ActivityLogQueries(self.db_manager)
        self.created_bundle_queries = CreatedBundleQueries(self.db_manager)

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

            # Create activity log for researcher
            research_activity_id = f"research-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=research_activity_id,
                activity_type="research",
                bundle_id=None,
                idea_id=None,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": mode, "focus": mode in ["focused", "research_only_focused"]})
            ))

            # Extract params for researcher
            focus = mode in ["focused", "research_only_focused"]
            niches = params.get("keyword", "") if focus else ""

            # Run researcher in thread pool (sync agent in async context)
            loop = asyncio.get_event_loop()
            research_results = await loop.run_in_executor(
                None,
                partial(self.researcher.execute, emit=emit, focus=focus, niches=niches)
            )

            # Mark activity as completed
            self.activity_queries.update_completion(research_activity_id, "completed", None)

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
            # Mark activity as failed if it was created
            if 'research_activity_id' in locals():
                self.activity_queries.update_completion(research_activity_id, "failed", str(e))

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

            # Create activity log for planner
            planner_activity_id = f"planner-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=planner_activity_id,
                activity_type="planner",
                bundle_id=None,  # Will be set after we get result
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=None
            ))

            # Run planner in thread pool (sync agent in async context)
            loop = asyncio.get_event_loop()
            planner_result = await loop.run_in_executor(
                None,
                partial(self.planner.execute, idea=idea_id, emit=emit)
            )

            # Mark activity as completed
            self.activity_queries.update_completion(planner_activity_id, "completed", None)

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
            # Mark activity as failed if it was created
            if 'planner_activity_id' in locals():
                self.activity_queries.update_completion(planner_activity_id, "failed", str(e))

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

            # Create activity log for maker
            maker_activity_id = f"maker-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=maker_activity_id,
                activity_type="maker",
                bundle_id=bundle_id,
                idea_id=bundle_record.idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=None
            ))

            # Run maker in thread pool (sync agent in async context)
            loop = asyncio.get_event_loop()
            maker_result = await loop.run_in_executor(
                None,
                partial(self.maker.execute, bundle_id=bundle_id, emit=emit)
            )

            # Mark activity as completed
            self.activity_queries.update_completion(maker_activity_id, "completed", None)

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
            # Mark activity as failed if it was created
            if 'maker_activity_id' in locals():
                self.activity_queries.update_completion(maker_activity_id, "failed", str(e))

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

    async def run_packager_from_bundle(
        self,
        bundle_id: str,
        emit: Callable[[Dict[str, Any]], None]
    ):
        """
        Run just the Packager step for an existing bundle
        Assumes bundle has completed maker step and has assets generated

        On successful completion, moves bundle to created_bundles archive

        Args:
            bundle_id: ID of the bundle to package
            emit: Callback to send events to frontend
        """
        logger.info(f"Starting Packager for bundle: {bundle_id}")
        emit({"event": "log", "step": "Orchestrator", "message": f"Packaging bundle {bundle_id}..."})

        try:
            # Validate bundle exists and has completed maker step
            bundle_record = self.bundle_queries.get_by_id(bundle_id)
            if not bundle_record:
                raise ValueError(f"Bundle not found: {bundle_id}")

            if bundle_record.current_step != "maker" or bundle_record.status != "completed":
                raise ValueError(f"Bundle {bundle_id} must complete maker step first (current: {bundle_record.current_step}/{bundle_record.status})")

            if not bundle_record.planner_output:
                raise ValueError(f"Bundle {bundle_id} has no planner output")

            # Parse planner output for metadata
            planner_data = json.loads(bundle_record.planner_output)

            # Step 1: Run packager with bundle_id
            emit({"event": "log", "step": "Packager", "message": "Creating final package..."})
            emit({"event": "progress", "step": "Packager", "pct": 0})

            # Create activity log for packager
            packager_activity_id = f"packager-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=packager_activity_id,
                activity_type="packager",
                bundle_id=bundle_id,
                idea_id=bundle_record.idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=None
            ))

            # TODO: Run actual packager agent when implemented
            # For now, simulate packaging by creating the archive record
            # loop = asyncio.get_event_loop()
            # packager_result = await loop.run_in_executor(
            #     None,
            #     partial(self.packager.execute, bundle_id=bundle_id, emit=emit)
            # )

            emit({"event": "log", "step": "Packager", "message": "Creating bundle archive..."})

            # Get bundle output directory
            bundle_dir = settings.get_bundle_dir(bundle_id)
            output_path = str(bundle_dir / "final_bundle.zip")  # Placeholder path

            # Create archived bundle record
            created_bundle = CreatedBundle(
                bundle_id=bundle_id,
                idea_id=bundle_record.idea_id,
                created_at=bundle_record.created_at,
                completed_at=datetime.now().isoformat(),
                planner_output=bundle_record.planner_output,
                maker_output=json.dumps({"status": "completed"}),  # Placeholder
                packager_output=json.dumps({"output_path": output_path}),  # Placeholder
                title=planner_data.get("title", "Untitled Bundle"),
                niche=planner_data.get("niche", "Unknown"),
                output_path=output_path
            )

            # Save to created_bundles table
            if not self.created_bundle_queries.create(created_bundle):
                raise ValueError(f"Failed to archive bundle {bundle_id}")

            # Delete from active bundles table
            if not self.bundle_queries.delete(bundle_id):
                logger.warning(f"Bundle archived but failed to remove from active table: {bundle_id}")

            # Mark activity as completed
            self.activity_queries.update_completion(packager_activity_id, "completed", None)

            emit({"event": "progress", "step": "Packager", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Packaging complete - bundle moved to archive"})

            # Emit done event
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": bundle_id,
                    "status": "Bundle packaged and archived successfully",
                    "output_path": output_path
                }
            })

        except Exception as e:
            # Mark activity as failed if it was created
            if 'packager_activity_id' in locals():
                self.activity_queries.update_completion(packager_activity_id, "failed", str(e))

            # Don't re-log the error here since agents already log it with their step name
            # Just emit error event and done status

            # Emit error event with step name for log display
            emit({"event": "error", "step": "Packager", "message": str(e)})

            # Emit done event with failure status (don't re-raise)
            emit({
                "event": "done",
                "success": False,
                "error": str(e)
            })