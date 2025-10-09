"""
Mock Maker Agent
Generates the assets and store metadata; runs QA (mock data)
"""

import asyncio
from typing import Dict, Any, Callable
from pathlib import Path
from app.logger import setup_logger

logger = setup_logger(__name__)


class MockMakerAgent:
    """Mock maker - generates fake assets and metadata"""

    async def execute(
        self,
        plan_data: Dict[str, Any],
        bundle_dir: Path,
        emit: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """Execute asset generation step with mock data"""

        # Emit progress
        for pct in [0, 25, 50, 75, 100]:
            emit({"event": "progress", "step": "Maker", "pct": pct})
            await asyncio.sleep(0.5)

        # Create assets directory
        assets_dir = bundle_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Mock asset generation
        generated_assets = []
        for asset in plan_data.get("assets", []):
            asset_file = assets_dir / f"{asset['name'].replace(' ', '_')}.{asset['format'].lower()}"
            asset_file.write_text(f"Mock {asset['type']} content for {asset['name']}")
            generated_assets.append({
                "name": asset["name"],
                "path": str(asset_file.relative_to(bundle_dir)),
                "size": asset_file.stat().st_size
            })

        # Generate marketplace metadata
        metadata = {
            "etsy": {
                "title": plan_data["title"],
                "description": plan_data["description"],
                "tags": plan_data["tags"][:13],  # Etsy limit
                "price": plan_data["pricing"]["base_price"]
            },
            "gumroad": {
                "name": plan_data["title"],
                "description": plan_data["description"],
                "price": plan_data["pricing"]["suggested_price"]
            }
        }

        # Mock QA check
        qa_report = {
            "status": "pass",
            "score": 0.93,
            "checks": {
                "assets_complete": True,
                "metadata_valid": True,
                "file_sizes_ok": True,
                "naming_convention": True
            }
        }

        emit({
            "event": "qa",
            "status": "pass",
            "score": qa_report["score"]
        })

        assets_data = {
            "generated_assets": generated_assets,
            "metadata": metadata,
            "qa_report": qa_report,
            "qa_score": qa_report["score"]  # Add for orchestrator
        }

        logger.info(f"[MOCK] Generated {len(generated_assets)} assets, QA score: {qa_report['score']}")
        return assets_data
