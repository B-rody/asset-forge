"""
Mock Planner Agent
Designs the bundle (plan, assets, pricing, personas) - mock data
"""

import asyncio
from typing import Dict, Any, Callable
from app.logger import setup_logger

logger = setup_logger(__name__)


class MockPlannerAgent:
    """Mock planner - returns fake bundle plans"""

    async def execute(
        self,
        research_data: Dict[str, Any],
        emit: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """Execute planning step with mock data"""

        # Emit progress
        for pct in [0, 25, 50, 75, 100]:
            emit({"event": "progress", "step": "Planner", "pct": pct})
            await asyncio.sleep(0.5)

        # Select top niche
        niches = research_data.get("niches", [])
        top_niche = niches[0] if niches else {"name": "Digital Templates"}

        # Mock plan data
        plan_data = {
            "niche": top_niche["name"],
            "title": f"{top_niche['name']} - Professional Bundle",
            "description": f"High-quality {top_niche['name']} designed for professionals",
            "pricing": {
                "base_price": 29.99,
                "suggested_price": 39.99,
                "premium_price": 49.99
            },
            "assets": [
                {"type": "template", "name": "Main Template", "format": "PDF"},
                {"type": "template", "name": "Variant 1", "format": "PDF"},
                {"type": "template", "name": "Variant 2", "format": "PDF"},
                {"type": "guide", "name": "Usage Guide", "format": "PDF"}
            ],
            "target_persona": {
                "age_range": "25-45",
                "occupation": "Professionals, Entrepreneurs",
                "pain_points": ["Time management", "Organization", "Productivity"]
            },
            "tags": ["productivity", "templates", "professional", "digital download"],
            "marketplaces": ["etsy", "gumroad"]
        }

        logger.info(f"[MOCK] Plan created: {plan_data['title']}")
        return plan_data
