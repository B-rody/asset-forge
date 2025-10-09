"""
Database models for bundle history
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BundleRecord(BaseModel):
    """Bundle execution record"""

    id: str = Field(..., description="Unique bundle identifier")
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    mode: str = Field(..., description="Pipeline mode (one_click, focused)")
    status: str = Field(default="pending", description="Bundle status (pending, running, completed, failed)")
    model: Optional[str] = Field(None, description="AI model used")
    output_path: Optional[str] = Field(None, description="Path to output bundle")
    keywords: Optional[str] = Field(None, description="User-provided keywords (for focused mode)")
    qa_score: Optional[float] = Field(None, description="QA score (0.0 - 1.0)")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "2025-10-07-one_click-bundle",
                "timestamp": 1633564800,
                "mode": "one_click",
                "status": "completed",
                "model": "gpt-4o",
                "output_path": "/data/bundles/2025-10-07-one_click-bundle/final_bundle.zip",
                "keywords": None,
                "qa_score": 0.93
            }
        }
