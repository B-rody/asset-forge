"""
Mock Researcher Agent
Finds and prioritizes profitable digital-product niches (mock data)
"""

import asyncio
from typing import Dict, Any, Callable
from app.logger import setup_logger

logger = setup_logger(__name__)


class MockResearcherAgent:
    """Mock researcher - returns fake niche data"""

    async def execute(
        self,
        mode: str,
        params: Dict[str, Any],
        emit: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """Execute research step with mock data"""

        # Emit progress
        for pct in [0, 25, 50, 75, 100]:
            emit({"event": "progress", "step": "Researcher", "pct": pct})
            await asyncio.sleep(0.5)  # Simulate work

        # Mock research data
        if mode == "focused":
            keyword = params.get("keyword", "digital templates")
            research_data = {
                "mode": "focused",
                "keyword": keyword,
                "niches": [
                    {
                        "name": f"{keyword} for professionals",
                        "score": 0.92,
                        "demand": "high",
                        "competition": "medium"
                    }
                ]
            }
        else:
            research_data = {
                "mode": "one_click",
                "niches": [
                    {
                        "name": "Notion templates for productivity",
                        "score": 0.95,
                        "demand": "very_high",
                        "competition": "medium"
                    },
                    {
                        "name": "Wedding invitation templates",
                        "score": 0.88,
                        "demand": "high",
                        "competition": "high"
                    }
                ]
            }

        logger.info(f"[MOCK] Research completed: {len(research_data['niches'])} niches found")
        return research_data
