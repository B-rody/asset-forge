"""
Mock Pipeline Orchestrator
Coordinates mock agents for testing and demos
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Callable
from pathlib import Path

from app.logger import setup_logger
from app.settings import settings
from app.database import DatabaseManager, BundleRecord, BundleQueries
from app.mock.agents.mock_researcher import MockResearcherAgent
from app.mock.agents.mock_asset_planner import MockPlannerAgent
from app.mock.agents.mock_asset_maker import MockMakerAgent
from app.mock.agents.mock_asset_packager import MockPackagerAgent

logger = setup_logger(__name__)


class MockPipelineOrchestrator:
    """Orchestrates mock pipeline execution for demos"""

    def __init__(self):
        self.researcher = MockResearcherAgent()
        self.planner = MockPlannerAgent()
        self.maker = MockMakerAgent()
        self.packager = MockPackagerAgent()

        # Initialize database
        self.db_manager = DatabaseManager(settings.db_path)
        self.bundle_queries = BundleQueries(self.db_manager)

    async def run_pipeline(
        self,
        mode: str,
        params: Dict[str, Any],
        emit: Callable[[Dict[str, Any]], None]
    ):
        """Run the complete mock pipeline"""
        bundle_id = None
        try:
            # Generate bundle ID
            timestamp = datetime.now().strftime("%Y-%m-%d")
            bundle_id = f"{timestamp}-{mode}-bundle"
            bundle_dir = settings.get_bundle_dir(bundle_id)

            # Create database record
            bundle_record = BundleRecord(
                id=bundle_id,
                mode=mode,
                status="running",
                model=params.get("model"),
                keywords=params.get("keyword")
            )
            self.bundle_queries.create(bundle_record)

            emit({
                "event": "log",
                "step": "Orchestrator",
                "message": f"[MOCK MODE] Starting pipeline in {mode} mode"
            })

            # Step 1: Research
            emit({"event": "log", "step": "Researcher", "message": "Analyzing market trends..."})
            research_data = await self.researcher.execute(mode, params, emit)
            self._save_step_output(bundle_dir, "research", research_data)

            # Step 2: Plan
            emit({"event": "log", "step": "Planner", "message": "Designing bundle..."})
            plan_data = await self.planner.execute(research_data, emit)
            self._save_step_output(bundle_dir, "plan", plan_data)

            # Step 3: Make
            emit({"event": "log", "step": "Maker", "message": "Generating assets..."})
            assets_data = await self.maker.execute(plan_data, bundle_dir, emit)
            self._save_step_output(bundle_dir, "assets", assets_data)

            # Step 4: Package
            emit({"event": "log", "step": "Packager", "message": "Creating final bundle..."})
            output_path = await self.packager.execute(
                bundle_dir, plan_data, assets_data, emit
            )

            # Extract QA score if available
            qa_score = assets_data.get("qa_score") if isinstance(assets_data, dict) else None

            # Update database with completion
            self.bundle_queries.update_completion(
                bundle_id=bundle_id,
                output_path=str(output_path),
                qa_score=qa_score
            )

            # Done!
            emit({
                "event": "done",
                "result": {
                    "bundle_id": bundle_id,
                    "output_path": str(output_path)
                }
            })

        except Exception as e:
            logger.error(f"[MOCK] Pipeline error: {e}", exc_info=True)

            # Update database with error
            if bundle_id:
                self.bundle_queries.update_status(
                    bundle_id=bundle_id,
                    status="failed",
                    error_message=str(e)
                )

            emit({
                "event": "error",
                "message": str(e)
            })

    async def re_run_step(
        self,
        bundle_id: str,
        step: str,
        emit: Callable[[Dict[str, Any]], None]
    ):
        """Re-run a specific pipeline step (mock)"""
        try:
            bundle_dir = settings.get_bundle_dir(bundle_id)

            emit({
                "event": "log",
                "step": step,
                "message": f"[MOCK MODE] Re-running {step}..."
            })

            # Load previous step data and re-execute
            if step == "Researcher":
                # Re-run from scratch
                await self.run_pipeline("one_click", {}, emit)
            elif step == "Planner":
                research_data = self._load_step_output(bundle_dir, "research")
                plan_data = await self.planner.execute(research_data, emit)
                self._save_step_output(bundle_dir, "plan", plan_data)
            elif step == "Maker":
                plan_data = self._load_step_output(bundle_dir, "plan")
                assets_data = await self.maker.execute(plan_data, bundle_dir, emit)
                self._save_step_output(bundle_dir, "assets", assets_data)
            elif step == "Packager":
                plan_data = self._load_step_output(bundle_dir, "plan")
                assets_data = self._load_step_output(bundle_dir, "assets")
                output_path = await self.packager.execute(
                    bundle_dir, plan_data, assets_data, emit
                )

            emit({
                "event": "done",
                "result": {"bundle_id": bundle_id}
            })

        except Exception as e:
            logger.error(f"[MOCK] Re-run error: {e}", exc_info=True)
            emit({
                "event": "error",
                "step": step,
                "message": str(e)
            })

    def _save_step_output(self, bundle_dir: Path, step: str, data: Dict[str, Any]):
        """Save step output to JSON file"""
        import orjson
        output_file = bundle_dir / f"{step}.json"
        output_file.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        logger.info(f"[MOCK] Saved {step} output to {output_file}")

    def _load_step_output(self, bundle_dir: Path, step: str) -> Dict[str, Any]:
        """Load step output from JSON file"""
        import orjson
        output_file = bundle_dir / f"{step}.json"
        return orjson.loads(output_file.read_bytes())
