"""
Database models for AssetForge pipeline
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Idea(BaseModel):
    """Active idea from research (not yet used for a bundle)"""

    idea_id: str = Field(..., description="Unique identifier from researcher")
    research_session_id: str = Field(..., description="Research session that produced this idea")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Quick filter fields
    title: str = Field(..., description="Product title")
    niche: str = Field(..., description="Primary market niche")
    sub_niche: str = Field(..., description="Specific sub-category")
    priority: str = Field(..., description="Priority tier: A, B, or C")
    roi_estimate: float = Field(..., description="ROI score from researcher")

    # Complete researcher output for this idea
    idea_json: str = Field(..., description="Full JSON of the idea from researcher")

    class Config:
        json_schema_extra = {
            "example": {
                "idea_id": "idea-2025-10-10-01",
                "research_session_id": "session-2025-10-10-001",
                "created_at": "2025-10-10T12:00:00",
                "title": "GLP-1 Journey Companion Bundle",
                "niche": "Health & wellness tracking",
                "sub_niche": "GLP-1 weight-loss therapy support",
                "priority": "A",
                "roi_estimate": 3.84,
                "idea_json": "{...}"
            }
        }


class Bundle(BaseModel):
    """Active bundle being produced through pipeline"""

    bundle_id: str = Field(..., description="Unique bundle identifier (from planner)")
    idea_id: str = Field(..., description="Source idea that became this bundle")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Pipeline state
    current_step: str = Field(..., description="Current step: planner, maker, or packager")
    status: str = Field(..., description="Status: pending, completed, or failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Step outputs
    planner_output: Optional[str] = Field(None, description="JSON output from planner")

    class Config:
        json_schema_extra = {
            "example": {
                "bundle_id": "bundle-2025-10-10-glp1-companion",
                "idea_id": "idea-2025-10-10-01",
                "created_at": "2025-10-10T12:00:00",
                "updated_at": "2025-10-10T12:30:00",
                "current_step": "planner",
                "status": "completed",
                "error_message": None,
                "planner_output": "{...}"
            }
        }


class MakerOutput(BaseModel):
    """Maker output tracking (assets created on disk)"""

    maker_id: str = Field(..., description="Unique maker output identifier")
    bundle_id: str = Field(..., description="Associated bundle")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Asset tracking
    output_dir: str = Field(..., description="Filesystem path where assets were created")
    maker_output: str = Field(..., description="Full JSON output from maker agent")

    # Packaging status
    is_packaged: bool = Field(default=False, description="Whether packager has completed")
    packaged_at: Optional[str] = Field(None, description="When packager completed")

    class Config:
        json_schema_extra = {
            "example": {
                "maker_id": "maker-2025-10-10-001",
                "bundle_id": "bundle-2025-10-10-glp1-companion",
                "created_at": "2025-10-10T13:00:00",
                "output_dir": "/data/2025-10-10-glp1-companion/maker_output",
                "maker_output": "{...}",
                "is_packaged": False,
                "packaged_at": None
            }
        }


class UsedIdea(BaseModel):
    """Archive of ideas that became bundles"""

    idea_id: str = Field(..., description="Original idea identifier")
    research_session_id: str = Field(..., description="Research session that produced this idea")
    created_at: str = Field(..., description="When idea was originally created")
    used_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    bundle_id: str = Field(..., description="Bundle that consumed this idea")

    # Same fields as Idea for reference
    title: str = Field(..., description="Product title")
    niche: str = Field(..., description="Primary market niche")
    sub_niche: str = Field(..., description="Specific sub-category")
    priority: str = Field(..., description="Priority tier: A, B, or C")
    roi_estimate: float = Field(..., description="ROI score from researcher")
    idea_json: str = Field(..., description="Full JSON of the idea from researcher")

    class Config:
        json_schema_extra = {
            "example": {
                "idea_id": "idea-2025-10-10-01",
                "research_session_id": "session-2025-10-10-001",
                "created_at": "2025-10-10T12:00:00",
                "used_at": "2025-10-10T15:00:00",
                "bundle_id": "bundle-2025-10-10-glp1-companion",
                "title": "GLP-1 Journey Companion Bundle",
                "niche": "Health & wellness tracking",
                "sub_niche": "GLP-1 weight-loss therapy support",
                "priority": "A",
                "roi_estimate": 3.84,
                "idea_json": "{...}"
            }
        }


class CreatedBundle(BaseModel):
    """Archive of completed bundles (ready to sell)"""

    bundle_id: str = Field(..., description="Bundle identifier")
    idea_id: str = Field(..., description="Source idea")
    created_at: str = Field(..., description="When bundle production started")
    completed_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # All step outputs
    planner_output: str = Field(..., description="JSON output from planner")
    maker_output: str = Field(..., description="JSON output from maker")
    packager_output: str = Field(..., description="JSON output from packager")

    # Quick metadata
    title: str = Field(..., description="Product title")
    niche: str = Field(..., description="Market niche")
    output_path: str = Field(..., description="Path to final bundle ZIP")

    class Config:
        json_schema_extra = {
            "example": {
                "bundle_id": "bundle-2025-10-10-glp1-companion",
                "idea_id": "idea-2025-10-10-01",
                "created_at": "2025-10-10T12:00:00",
                "completed_at": "2025-10-10T15:00:00",
                "planner_output": "{...}",
                "maker_output": "{...}",
                "packager_output": "{...}",
                "title": "GLP-1 Journey Companion Bundle",
                "niche": "Health & wellness tracking",
                "output_path": "/data/2025-10-10-glp1-companion/final_bundle.zip"
            }
        }


class ResearchSession(BaseModel):
    """Research session metadata"""

    session_id: str = Field(..., description="Unique session identifier")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    idea_count: int = Field(..., description="Number of ideas generated")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session-2025-10-10-001",
                "created_at": "2025-10-10T12:00:00",
                "idea_count": 9
            }
        }


class ActivityLog(BaseModel):
    """Activity log for tracking all pipeline activities"""

    activity_id: str = Field(..., description="Unique activity identifier")
    activity_type: str = Field(..., description="Type: research, planner, maker, packager")
    bundle_id: Optional[str] = Field(None, description="Associated bundle (nullable for research)")
    idea_id: Optional[str] = Field(None, description="Associated idea (nullable)")
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = Field(None, description="When activity completed")
    status: str = Field(..., description="Status: in_progress, completed, failed")
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata_json: Optional[str] = Field(None, description="Activity-specific metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "activity_id": "research-2025-10-13-001",
                "activity_type": "research",
                "bundle_id": None,
                "idea_id": None,
                "started_at": "2025-10-13T12:00:00",
                "completed_at": "2025-10-13T12:05:30",
                "status": "completed",
                "duration_seconds": 330,
                "error_message": None,
                "metadata_json": "{\"idea_count\": 9}"
            }
        }
