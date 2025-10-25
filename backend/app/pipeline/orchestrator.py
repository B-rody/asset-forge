"""
Pipeline Orchestrator
Coordinates the execution of all pipeline agents using OpenAI
"""

import asyncio
import json
import os
from datetime import datetime
from functools import partial
from typing import Dict, Any, Callable
from pathlib import Path
from uuid import uuid4

from app.logger import setup_logger
from app.settings import settings
from app.database import DatabaseManager, BundleQueries
from app.database.queries import ActivityLogQueries, CreatedBundleQueries, IdeaQueries, UsedIdeaQueries
from app.database.models import ActivityLog, CreatedBundle, UsedIdea
from app.pipeline.agents.researcher import ResearcherAgent
from app.pipeline.agents.asset_agents.asset_planner import PlannerAgent
from app.pipeline.agents.asset_agents.asset_maker import MakerAgent
from app.pipeline.agents.asset_agents.asset_packager import PackagerAgent

logger = setup_logger(__name__)

# ============================================================================
# DEBUG MODE: Force API Failures for Testing
# ============================================================================
# Set environment variable DEBUG_FORCE_FAILURE to force failures at specific steps.
# This is useful for testing error handling, database state transitions, and retry logic.
#
# Usage:
#   Windows CMD:
#     set DEBUG_FORCE_FAILURE=planner
#     pnpm dev
#
#   Windows PowerShell:
#     $env:DEBUG_FORCE_FAILURE="planner"
#     pnpm dev
#
#   Normal mode (no debug failures):
#     pnpm dev
#
# Valid values: "researcher", "planner", "maker", "packager", or None (disabled)
# ============================================================================
_DEBUG_FORCE_FAILURE_AT_STEP = os.getenv("DEBUG_FORCE_FAILURE", None)

if _DEBUG_FORCE_FAILURE_AT_STEP:
    logger.warning(f"⚠️  DEBUG MODE ACTIVE: Will force failure at step '{_DEBUG_FORCE_FAILURE_AT_STEP}'")
    logger.warning(f"⚠️  This is for testing only. Unset DEBUG_FORCE_FAILURE to disable.")


class PipelineOrchestrator:
    """Orchestrates the execution of all pipeline steps with real OpenAI integration"""

    def __init__(self):
        # Initialize database
        self.db_manager = DatabaseManager(settings.db_path)
        self.bundle_queries = BundleQueries(self.db_manager)
        self.activity_queries = ActivityLogQueries(self.db_manager)
        self.created_bundle_queries = CreatedBundleQueries(self.db_manager)
        self.idea_queries = IdeaQueries(self.db_manager)
        self.used_idea_queries = UsedIdeaQueries(self.db_manager)

        # Initialize agents with database access
        self.researcher = ResearcherAgent(db_manager=self.db_manager)
        self.planner = PlannerAgent(db_manager=self.db_manager)
        self.maker = MakerAgent(db_manager=self.db_manager)
        self.packager = PackagerAgent(db_manager=self.db_manager)

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

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "researcher":
                logger.warning("⚠️  DEBUG: Forcing failure at Researcher step")
                raise Exception("DEBUG MODE: Forced failure at Researcher step for testing error handling")

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
                ideas_count = len(research_results.get("ideas", [])) if isinstance(research_results, dict) else 0
                emit({
                    "event": "done",
                    "success": True,
                    "research_only": True,
                    "result": {
                        "ideas_count": ideas_count,
                        "message": f"{ideas_count} ideas generated",
                        "research": research_results,
                        "mode": "research"
                    }
                })
                return

            # Full automation: Continue with planner, maker, packager
            emit({"event": "log", "step": "Orchestrator", "message": "Selecting best idea for bundle creation..."})

            # Step 2: Select best idea (highest priority)
            ideas = research_results.get("ideas", [])
            if not ideas:
                raise ValueError("No ideas generated by researcher")

            # Sort by priority (assuming higher is better) and take top idea
            best_idea = max(ideas, key=lambda x: x.get("priority", 0))
            idea_title = best_idea.get("title", "Unknown")

            # Get idea_id directly from researcher result (DB-generated ID)
            # The researcher now adds 'idea_id' to each idea after saving to DB
            idea_id = best_idea.get("idea_id")

            if not idea_id:
                raise ValueError(f"Could not find saved idea ID for: {idea_title}. Database save may have failed.")

            emit({"event": "log", "step": "Orchestrator", "message": f"Selected idea: {idea_title} (ID: {idea_id})"})

            # Step 3: Run planner
            emit({"event": "log", "step": "Planner", "message": "Designing bundle..."})
            emit({"event": "progress", "step": "Planner", "pct": 0})

            planner_activity_id = f"planner-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=planner_activity_id,
                activity_type="planner",
                bundle_id=None,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": mode})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "planner":
                logger.warning("⚠️  DEBUG: Forcing failure at Planner step")
                raise Exception("DEBUG MODE: Forced failure at Planner step for testing error handling")

            planner_result = await loop.run_in_executor(
                None,
                partial(self.planner.execute, idea=idea_id, emit=emit)
            )

            self.activity_queries.update_completion(planner_activity_id, "completed", None)
            emit({"event": "progress", "step": "Planner", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Bundle planning complete"})

            bundle_id = planner_result.get("bundle_id")
            bundle_title = planner_result.get("title", "Untitled Bundle")

            # Step 4: Run maker
            emit({"event": "log", "step": "Maker", "message": "Generating assets..."})
            emit({"event": "progress", "step": "Maker", "pct": 0})

            maker_activity_id = f"maker-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=maker_activity_id,
                activity_type="maker",
                bundle_id=bundle_id,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": mode})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "maker":
                logger.warning("⚠️  DEBUG: Forcing failure at Maker step")
                raise Exception("DEBUG MODE: Forced failure at Maker step for testing error handling")

            maker_result = await loop.run_in_executor(
                None,
                partial(self.maker.execute, bundle_id=bundle_id, emit=emit)
            )

            self.activity_queries.update_completion(maker_activity_id, "completed", None)
            emit({"event": "progress", "step": "Maker", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Asset generation complete"})

            # Step 5: Run packager
            emit({"event": "log", "step": "Packager", "message": "Packaging bundle..."})
            emit({"event": "progress", "step": "Packager", "pct": 0})

            packager_activity_id = f"packager-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=packager_activity_id,
                activity_type="packager",
                bundle_id=bundle_id,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": mode})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "packager":
                logger.warning("⚠️  DEBUG: Forcing failure at Packager step")
                raise Exception("DEBUG MODE: Forced failure at Packager step for testing error handling")

            packager_result = await loop.run_in_executor(
                None,
                partial(self.packager.execute, bundle_id=bundle_id, emit=emit)
            )

            self.activity_queries.update_completion(packager_activity_id, "completed", None)
            emit({"event": "progress", "step": "Packager", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Bundle packaging complete"})

            # Archive bundle
            emit({"event": "log", "step": "Orchestrator", "message": "Archiving bundle..."})

            bundle_record = self.bundle_queries.get_by_id(bundle_id)
            if not bundle_record:
                raise ValueError(f"Bundle not found: {bundle_id}")

            planner_data = json.loads(bundle_record.planner_output)

            # Use final output path from packager result (user's configured output_dir)
            final_output_path = packager_result.get("final_output_path")
            if not final_output_path:
                # Fallback to bundle_dir if packager didn't return final_output_path
                bundle_dir = settings.get_bundle_dir(bundle_id)
                final_output_path = str(bundle_dir)

            created_bundle = CreatedBundle(
                bundle_id=bundle_id,
                idea_id=idea_id,
                created_at=bundle_record.created_at,
                completed_at=datetime.now().isoformat(),
                planner_output=bundle_record.planner_output,
                maker_output=json.dumps({"status": "completed"}),
                packager_output=json.dumps(packager_result),
                title=planner_data.get("title", "Untitled Bundle"),
                niche=planner_data.get("niche", "Unknown"),
                output_path=final_output_path
            )

            if not self.created_bundle_queries.create(created_bundle):
                raise ValueError(f"Failed to archive bundle {bundle_id}")

            # Delete from active bundles table - only after successful archiving
            # This is the final cleanup step
            if not self.bundle_queries.delete(bundle_id):
                # This is a warning, not a critical error - bundle is already archived
                logger.warning(f"Bundle archived successfully but failed to remove from active table: {bundle_id}")
                logger.warning(f"Manual cleanup may be required for bundle_id: {bundle_id}")

            emit({"event": "log", "step": "Orchestrator", "message": "Full pipeline complete!"})

            # Emit final done event
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": bundle_id,
                    "bundle_title": bundle_title,
                    "output_path": final_output_path,
                    "store_title": packager_result.get("store_title"),
                    "store_description": packager_result.get("store_description"),
                    "converted_pdfs": len(packager_result.get("converted_pdfs", [])),
                    "message": f"Complete bundle created: {packager_result.get('store_title', bundle_title)}",
                    "mode": "auto"
                }
            })

        except Exception as e:
            # Mark activities as failed and determine which step failed
            failed_step = "Orchestrator"
            bundle_id_to_fail = None

            if 'packager_activity_id' in locals():
                self.activity_queries.update_completion(packager_activity_id, "failed", str(e))
                failed_step = "Packager"
                bundle_id_to_fail = locals().get('bundle_id')
            elif 'maker_activity_id' in locals():
                self.activity_queries.update_completion(maker_activity_id, "failed", str(e))
                failed_step = "Maker"
                bundle_id_to_fail = locals().get('bundle_id')
            elif 'planner_activity_id' in locals():
                self.activity_queries.update_completion(planner_activity_id, "failed", str(e))
                failed_step = "Planner"
                bundle_id_to_fail = locals().get('bundle_id')
            elif 'research_activity_id' in locals():
                self.activity_queries.update_completion(research_activity_id, "failed", str(e))
                failed_step = "Researcher"
                # No bundle_id yet for researcher failures

            # Update bundle status to failed if we have a bundle_id
            # Keep current step unchanged - only update status to "failed"
            if bundle_id_to_fail:
                bundle_record = self.bundle_queries.get_by_id(bundle_id_to_fail)
                if bundle_record:
                    self.bundle_queries.update_step(bundle_id_to_fail, bundle_record.current_step, "failed", str(e))

            # Don't emit separate error event - the done event already contains the error
            # This prevents duplicate error messages in the UI
            # (Agents may emit their own error events before raising, but orchestrator just handles cleanup)

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

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "planner":
                logger.warning("⚠️  DEBUG: Forcing failure at Planner step")
                raise Exception("DEBUG MODE: Forced failure at Planner step for testing error handling")

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

            # Emit done event with bundle title
            bundle_title = planner_result.get("title", "Untitled Bundle")
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": planner_result.get("bundle_id", "unknown"),
                    "bundle_title": bundle_title,
                    "idea_id": idea_id,
                    "message": f"Bundle plan created: {bundle_title}",
                    "planner": planner_result,
                    "mode": "plan"
                }
            })

        except Exception as e:
            # Mark activity as failed if it was created
            if 'planner_activity_id' in locals():
                self.activity_queries.update_completion(planner_activity_id, "failed", str(e))

            # Update bundle status to failed if we have a bundle_id
            # Planner creates bundle, so we need to check if it was created before failure
            # Keep current step unchanged - only update status to "failed"
            bundle_id_to_fail = locals().get('planner_result', {}).get('bundle_id')
            if bundle_id_to_fail:
                bundle_record = self.bundle_queries.get_by_id(bundle_id_to_fail)
                if bundle_record:
                    self.bundle_queries.update_step(bundle_id_to_fail, bundle_record.current_step, "failed", str(e))

            # Don't emit separate error event - the done event already contains the error
            # This prevents duplicate error messages in the UI
            # (Agents may emit their own error events before raising, but orchestrator just handles cleanup)

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

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "maker":
                logger.warning("⚠️  DEBUG: Forcing failure at Maker step")
                raise Exception("DEBUG MODE: Forced failure at Maker step for testing error handling")

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

            # Count files in maker_output directory
            bundle_dir = settings.get_bundle_dir(bundle_id)
            maker_output_dir = bundle_dir / "maker_output"
            file_count = 0
            if maker_output_dir.exists():
                file_count = sum(1 for f in maker_output_dir.rglob('*') if f.is_file())

            # Get bundle title from planner output
            bundle_title = "Unknown"
            try:
                planner_data = json.loads(bundle_record.planner_output)
                bundle_title = planner_data.get("title", "Unknown")
            except:
                pass

            # Emit done event with file count and output path
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": bundle_id,
                    "bundle_title": bundle_title,
                    "file_count": file_count,
                    "output_path": str(maker_output_dir),
                    "message": f"Assets generated - {file_count} files created",
                    "mode": "maker"
                }
            })

        except Exception as e:
            # Mark activity as failed if it was created
            if 'maker_activity_id' in locals():
                self.activity_queries.update_completion(maker_activity_id, "failed", str(e))

            # Update bundle status to failed - keep current step unchanged
            # Maker runs when bundle is at step="maker", so keep it there with status="failed"
            bundle_record = self.bundle_queries.get_by_id(bundle_id)
            if bundle_record:
                self.bundle_queries.update_step(bundle_id, bundle_record.current_step, "failed", str(e))

            # Don't emit separate error event - the done event already contains the error
            # This prevents duplicate error messages in the UI
            # (Agents may emit their own error events before raising, but orchestrator just handles cleanup)

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
            # Validate bundle exists and is at packager step
            bundle_record = self.bundle_queries.get_by_id(bundle_id)
            if not bundle_record:
                raise ValueError(f"Bundle not found: {bundle_id}")

            if bundle_record.current_step != "packager":
                raise ValueError(f"Bundle {bundle_id} must be at packager step (current: {bundle_record.current_step}/{bundle_record.status})")

            if not bundle_record.planner_output:
                raise ValueError(f"Bundle {bundle_id} has no planner output")

            # Parse planner output for metadata
            planner_data = json.loads(bundle_record.planner_output)

            # Step 1: Run packager with bundle_id
            print("[EMIT] log | step=Packager | message=Creating final package...")
            emit({"event": "log", "step": "Packager", "message": "Creating final package..."})
            print("[EMIT] progress | step=Packager | pct=0")
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

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "packager":
                logger.warning("⚠️  DEBUG: Forcing failure at Packager step")
                raise Exception("DEBUG MODE: Forced failure at Packager step for testing error handling")

            # Run packager in thread pool (sync agent in async context)
            loop = asyncio.get_event_loop()
            packager_result = await loop.run_in_executor(
                None,
                partial(self.packager.execute, bundle_id=bundle_id, emit=emit)
            )

            print("[EMIT] log | step=Packager | message=Creating bundle archive...")
            emit({"event": "log", "step": "Packager", "message": "Creating bundle archive..."})

            # Use final output path from packager result (user's configured output_dir)
            final_output_path = packager_result.get("final_output_path")
            if not final_output_path:
                # Fallback to bundle_dir if packager didn't return final_output_path
                bundle_dir = settings.get_bundle_dir(bundle_id)
                final_output_path = str(bundle_dir)

            # Create archived bundle record with actual packager results
            created_bundle = CreatedBundle(
                bundle_id=bundle_id,
                idea_id=bundle_record.idea_id,
                created_at=bundle_record.created_at,
                completed_at=datetime.now().isoformat(),
                planner_output=bundle_record.planner_output,
                maker_output=json.dumps({"status": "completed"}),
                packager_output=json.dumps(packager_result),
                title=planner_data.get("title", "Untitled Bundle"),
                niche=planner_data.get("niche", "Unknown"),
                output_path=final_output_path
            )

            # Save to created_bundles table
            if not self.created_bundle_queries.create(created_bundle):
                raise ValueError(f"Failed to archive bundle {bundle_id}")

            # Mark activity as completed BEFORE deleting from active table
            # This ensures activity log is complete even if deletion fails
            self.activity_queries.update_completion(packager_activity_id, "completed", None)

            # Delete from active bundles table - only after successful archiving
            # This is the final cleanup step
            if not self.bundle_queries.delete(bundle_id):
                # This is a warning, not a critical error - bundle is already archived
                logger.warning(f"Bundle archived successfully but failed to remove from active table: {bundle_id}")
                logger.warning(f"Manual cleanup may be required for bundle_id: {bundle_id}")

            print("[EMIT] progress | step=Packager | pct=100")
            emit({"event": "progress", "step": "Packager", "pct": 100})
            print("[EMIT] log | step=Orchestrator | message=Packaging complete - bundle moved to archive")
            emit({"event": "log", "step": "Orchestrator", "message": "Packaging complete - bundle moved to archive"})

            # Emit done event with packager results
            bundle_title = planner_data.get("title", "Untitled Bundle")
            print(f"[EMIT] done | success=True | bundle_id={bundle_id}")
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": bundle_id,
                    "bundle_title": bundle_title,
                    "output_path": final_output_path,
                    "store_title": packager_result.get("store_title"),
                    "store_description": packager_result.get("store_description"),
                    "converted_pdfs": len(packager_result.get("converted_pdfs", [])),
                    "message": f"Bundle packaged and ready: {packager_result.get('store_title', bundle_title)}",
                    "mode": "packager"
                }
            })

        except Exception as e:
            # Mark activity as failed if it was created
            if 'packager_activity_id' in locals():
                self.activity_queries.update_completion(packager_activity_id, "failed", str(e))

            # Update bundle status to failed - keep current step unchanged
            # Packager runs when bundle is at step="packager", so keep it there with status="failed"
            bundle_record = self.bundle_queries.get_by_id(bundle_id)
            if bundle_record:
                self.bundle_queries.update_step(bundle_id, bundle_record.current_step, "failed", str(e))

            # Don't emit separate error event - the done event already contains the error
            # This prevents duplicate error messages in the UI
            # (Agents may emit their own error events before raising, but orchestrator just handles cleanup)

            # Emit done event with failure status (don't re-raise)
            emit({
                "event": "done",
                "success": False,
                "error": str(e)
            })

    async def run_auto_from_existing_idea(
        self,
        emit: Callable[[Dict[str, Any]], None]
    ):
        """
        Run full auto pipeline using best available existing idea
        Skips research, goes straight to Planner → Maker → Packager

        This is the "Quick Build" flow that uses existing idea inventory

        Args:
            emit: Callback to send events to frontend
        """
        logger.info("Starting quick build from existing idea")
        emit({"event": "log", "step": "Orchestrator", "message": "Quick Build: Selecting best available idea..."})

        try:
            # Step 1: Query available ideas (priority A/B, recent 8 weeks)
            available_ideas = self.idea_queries.get_available_ideas(weeks_back=8, priorities=["A", "B"])

            if not available_ideas:
                raise ValueError("No available ideas found. Please run research first.")

            # Step 2: Select best idea by priority (A > B) then ROI
            # Priority is string "A", "B", "C" - A is best
            priority_rank = {"A": 3, "B": 2, "C": 1}
            best_idea = max(
                available_ideas,
                key=lambda x: (priority_rank.get(x.priority, 0), x.roi_estimate or 0)
            )

            idea_id = best_idea.idea_id
            idea_title = best_idea.title
            emit({"event": "log", "step": "Orchestrator", "message": f"Selected idea: {idea_title} (Priority {best_idea.priority}, ROI: {best_idea.roi_estimate})"})

            # Step 3: Run planner
            emit({"event": "log", "step": "Planner", "message": "Designing bundle..."})
            emit({"event": "progress", "step": "Planner", "pct": 0})

            planner_activity_id = f"planner-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=planner_activity_id,
                activity_type="planner",
                bundle_id=None,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": "quick_build"})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "planner":
                logger.warning("⚠️  DEBUG: Forcing failure at Planner step")
                raise Exception("DEBUG MODE: Forced failure at Planner step for testing error handling")

            loop = asyncio.get_event_loop()
            planner_result = await loop.run_in_executor(
                None,
                partial(self.planner.execute, idea=idea_id, emit=emit)
            )

            self.activity_queries.update_completion(planner_activity_id, "completed", None)
            emit({"event": "progress", "step": "Planner", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Bundle planning complete"})

            bundle_id = planner_result.get("bundle_id")
            bundle_title = planner_result.get("title", "Untitled Bundle")

            # Step 4: Run maker
            emit({"event": "log", "step": "Maker", "message": "Generating assets..."})
            emit({"event": "progress", "step": "Maker", "pct": 0})

            maker_activity_id = f"maker-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=maker_activity_id,
                activity_type="maker",
                bundle_id=bundle_id,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": "quick_build"})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "maker":
                logger.warning("⚠️  DEBUG: Forcing failure at Maker step")
                raise Exception("DEBUG MODE: Forced failure at Maker step for testing error handling")

            maker_result = await loop.run_in_executor(
                None,
                partial(self.maker.execute, bundle_id=bundle_id, emit=emit)
            )

            self.activity_queries.update_completion(maker_activity_id, "completed", None)
            emit({"event": "progress", "step": "Maker", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Asset generation complete"})

            # Step 5: Run packager
            emit({"event": "log", "step": "Packager", "message": "Packaging bundle..."})
            emit({"event": "progress", "step": "Packager", "pct": 0})

            packager_activity_id = f"packager-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=packager_activity_id,
                activity_type="packager",
                bundle_id=bundle_id,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": "quick_build"})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "packager":
                logger.warning("⚠️  DEBUG: Forcing failure at Packager step")
                raise Exception("DEBUG MODE: Forced failure at Packager step for testing error handling")

            packager_result = await loop.run_in_executor(
                None,
                partial(self.packager.execute, bundle_id=bundle_id, emit=emit)
            )

            self.activity_queries.update_completion(packager_activity_id, "completed", None)
            emit({"event": "progress", "step": "Packager", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Bundle packaging complete"})

            # Step 6: Archive bundle
            emit({"event": "log", "step": "Orchestrator", "message": "Archiving bundle..."})

            bundle_record = self.bundle_queries.get_by_id(bundle_id)
            if not bundle_record:
                raise ValueError(f"Bundle not found: {bundle_id}")

            planner_data = json.loads(bundle_record.planner_output)

            # Use final output path from packager result
            final_output_path = packager_result.get("final_output_path")
            if not final_output_path:
                bundle_dir = settings.get_bundle_dir(bundle_id)
                final_output_path = str(bundle_dir)

            created_bundle = CreatedBundle(
                bundle_id=bundle_id,
                idea_id=idea_id,
                created_at=bundle_record.created_at,
                completed_at=datetime.now().isoformat(),
                planner_output=bundle_record.planner_output,
                maker_output=json.dumps({"status": "completed"}),
                packager_output=json.dumps(packager_result),
                title=planner_data.get("title", "Untitled Bundle"),
                niche=planner_data.get("niche", "Unknown"),
                output_path=final_output_path
            )

            if not self.created_bundle_queries.create(created_bundle):
                raise ValueError(f"Failed to archive bundle {bundle_id}")

            # Delete from active bundles table
            if not self.bundle_queries.delete(bundle_id):
                logger.warning(f"Bundle archived successfully but failed to remove from active table: {bundle_id}")

            emit({"event": "log", "step": "Orchestrator", "message": "Quick Build complete!"})

            # Emit final done event
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": bundle_id,
                    "bundle_title": bundle_title,
                    "output_path": final_output_path,
                    "store_title": packager_result.get("store_title"),
                    "store_description": packager_result.get("store_description"),
                    "converted_pdfs": len(packager_result.get("converted_pdfs", [])),
                    "message": f"Quick Build complete: {packager_result.get('store_title', bundle_title)}",
                    "mode": "auto"
                }
            })

        except Exception as e:
            # Mark activities as failed and determine which step failed
            failed_step = "Orchestrator"
            bundle_id_to_fail = None

            if 'packager_activity_id' in locals():
                self.activity_queries.update_completion(packager_activity_id, "failed", str(e))
                failed_step = "Packager"
                bundle_id_to_fail = locals().get('bundle_id')
            elif 'maker_activity_id' in locals():
                self.activity_queries.update_completion(maker_activity_id, "failed", str(e))
                failed_step = "Maker"
                bundle_id_to_fail = locals().get('bundle_id')
            elif 'planner_activity_id' in locals():
                self.activity_queries.update_completion(planner_activity_id, "failed", str(e))
                failed_step = "Planner"
                bundle_id_to_fail = locals().get('bundle_id')

            # Update bundle status to failed if we have a bundle_id
            # Keep current step unchanged - only update status to "failed"
            if bundle_id_to_fail:
                bundle_record = self.bundle_queries.get_by_id(bundle_id_to_fail)
                if bundle_record:
                    self.bundle_queries.update_step(bundle_id_to_fail, bundle_record.current_step, "failed", str(e))

            # Don't emit separate error event - the done event already contains the error
            # This prevents duplicate error messages in the UI
            # (Agents may emit their own error events before raising, but orchestrator just handles cleanup)

            # Emit done event with failure status
            emit({
                "event": "done",
                "success": False,
                "error": str(e)
            })

    async def run_full_from_idea(
        self,
        idea_id: str,
        emit: Callable[[Dict[str, Any]], None]
    ):
        """
        Run full pipeline (Planner → Maker → Packager) from a specific idea
        Skips research, uses manually selected idea

        This is the "Browse & Select" flow that gives users full control

        Args:
            idea_id: ID of the manually selected idea
            emit: Callback to send events to frontend
        """
        logger.info(f"Starting full pipeline from selected idea: {idea_id}")
        emit({"event": "log", "step": "Orchestrator", "message": f"Building complete bundle from idea {idea_id}..."})

        try:
            # Step 1: Validate idea exists
            idea_record = self.idea_queries.get_by_id(idea_id)
            if not idea_record:
                raise ValueError(f"Idea not found: {idea_id}")

            idea_title = idea_record.title
            emit({"event": "log", "step": "Orchestrator", "message": f"Using idea: {idea_title}"})

            # Step 2: Run planner
            emit({"event": "log", "step": "Planner", "message": "Designing bundle..."})
            emit({"event": "progress", "step": "Planner", "pct": 0})

            planner_activity_id = f"planner-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=planner_activity_id,
                activity_type="planner",
                bundle_id=None,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": "manual_full_build"})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "planner":
                logger.warning("⚠️  DEBUG: Forcing failure at Planner step")
                raise Exception("DEBUG MODE: Forced failure at Planner step for testing error handling")

            loop = asyncio.get_event_loop()
            planner_result = await loop.run_in_executor(
                None,
                partial(self.planner.execute, idea=idea_id, emit=emit)
            )

            self.activity_queries.update_completion(planner_activity_id, "completed", None)
            emit({"event": "progress", "step": "Planner", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Bundle planning complete"})

            bundle_id = planner_result.get("bundle_id")
            bundle_title = planner_result.get("title", "Untitled Bundle")

            # Step 3: Run maker
            emit({"event": "log", "step": "Maker", "message": "Generating assets..."})
            emit({"event": "progress", "step": "Maker", "pct": 0})

            maker_activity_id = f"maker-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=maker_activity_id,
                activity_type="maker",
                bundle_id=bundle_id,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": "manual_full_build"})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "maker":
                logger.warning("⚠️  DEBUG: Forcing failure at Maker step")
                raise Exception("DEBUG MODE: Forced failure at Maker step for testing error handling")

            maker_result = await loop.run_in_executor(
                None,
                partial(self.maker.execute, bundle_id=bundle_id, emit=emit)
            )

            self.activity_queries.update_completion(maker_activity_id, "completed", None)
            emit({"event": "progress", "step": "Maker", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Asset generation complete"})

            # Step 4: Run packager
            emit({"event": "log", "step": "Packager", "message": "Packaging bundle..."})
            emit({"event": "progress", "step": "Packager", "pct": 0})

            packager_activity_id = f"packager-{uuid4().hex[:8]}"
            self.activity_queries.create(ActivityLog(
                activity_id=packager_activity_id,
                activity_type="packager",
                bundle_id=bundle_id,
                idea_id=idea_id,
                started_at=datetime.now().isoformat(),
                completed_at=None,
                status="in_progress",
                duration_seconds=None,
                error_message=None,
                metadata_json=json.dumps({"mode": "manual_full_build"})
            ))

            # DEBUG: Force failure if configured
            if _DEBUG_FORCE_FAILURE_AT_STEP == "packager":
                logger.warning("⚠️  DEBUG: Forcing failure at Packager step")
                raise Exception("DEBUG MODE: Forced failure at Packager step for testing error handling")

            packager_result = await loop.run_in_executor(
                None,
                partial(self.packager.execute, bundle_id=bundle_id, emit=emit)
            )

            self.activity_queries.update_completion(packager_activity_id, "completed", None)
            emit({"event": "progress", "step": "Packager", "pct": 100})
            emit({"event": "log", "step": "Orchestrator", "message": "Bundle packaging complete"})

            # Step 5: Archive bundle
            emit({"event": "log", "step": "Orchestrator", "message": "Archiving bundle..."})

            bundle_record = self.bundle_queries.get_by_id(bundle_id)
            if not bundle_record:
                raise ValueError(f"Bundle not found: {bundle_id}")

            planner_data = json.loads(bundle_record.planner_output)

            # Use final output path from packager result
            final_output_path = packager_result.get("final_output_path")
            if not final_output_path:
                bundle_dir = settings.get_bundle_dir(bundle_id)
                final_output_path = str(bundle_dir)

            created_bundle = CreatedBundle(
                bundle_id=bundle_id,
                idea_id=idea_id,
                created_at=bundle_record.created_at,
                completed_at=datetime.now().isoformat(),
                planner_output=bundle_record.planner_output,
                maker_output=json.dumps({"status": "completed"}),
                packager_output=json.dumps(packager_result),
                title=planner_data.get("title", "Untitled Bundle"),
                niche=planner_data.get("niche", "Unknown"),
                output_path=final_output_path
            )

            if not self.created_bundle_queries.create(created_bundle):
                raise ValueError(f"Failed to archive bundle {bundle_id}")

            # Delete from active bundles table
            if not self.bundle_queries.delete(bundle_id):
                logger.warning(f"Bundle archived successfully but failed to remove from active table: {bundle_id}")

            emit({"event": "log", "step": "Orchestrator", "message": "Complete bundle generated!"})

            # Emit final done event
            emit({
                "event": "done",
                "success": True,
                "result": {
                    "bundle_id": bundle_id,
                    "bundle_title": bundle_title,
                    "output_path": final_output_path,
                    "store_title": packager_result.get("store_title"),
                    "store_description": packager_result.get("store_description"),
                    "converted_pdfs": len(packager_result.get("converted_pdfs", [])),
                    "message": f"Complete bundle generated: {packager_result.get('store_title', bundle_title)}",
                    "mode": "auto"
                }
            })

        except Exception as e:
            # Mark activities as failed and determine which step failed
            failed_step = "Orchestrator"
            bundle_id_to_fail = None

            if 'packager_activity_id' in locals():
                self.activity_queries.update_completion(packager_activity_id, "failed", str(e))
                failed_step = "Packager"
                bundle_id_to_fail = locals().get('bundle_id')
            elif 'maker_activity_id' in locals():
                self.activity_queries.update_completion(maker_activity_id, "failed", str(e))
                failed_step = "Maker"
                bundle_id_to_fail = locals().get('bundle_id')
            elif 'planner_activity_id' in locals():
                self.activity_queries.update_completion(planner_activity_id, "failed", str(e))
                failed_step = "Planner"
                bundle_id_to_fail = locals().get('bundle_id')

            # Update bundle status to failed if we have a bundle_id
            # Keep current step unchanged - only update status to "failed"
            if bundle_id_to_fail:
                bundle_record = self.bundle_queries.get_by_id(bundle_id_to_fail)
                if bundle_record:
                    self.bundle_queries.update_step(bundle_id_to_fail, bundle_record.current_step, "failed", str(e))

            # Don't emit separate error event - the done event already contains the error
            # This prevents duplicate error messages in the UI
            # (Agents may emit their own error events before raising, but orchestrator just handles cleanup)

            # Emit done event with failure status
            emit({
                "event": "done",
                "success": False,
                "error": str(e)
            })
