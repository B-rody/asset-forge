"""
Maker Agent
Generates digital product assets with built-in self-QA validation
"""

import json
import re
from typing import Dict, Any, Callable, Optional, Union, TYPE_CHECKING
from datetime import datetime
from pathlib import Path
from app.pipeline.agents.base_agent import BaseAgent

if TYPE_CHECKING:
    from app.database.db import DatabaseManager


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use in Windows/Unix filenames.

    Removes or replaces characters that are invalid in Windows paths:
    < > : " / \ | ? *

    Also removes control characters and collapses multiple dashes/spaces.

    Args:
        name: The filename or directory name to sanitize

    Returns:
        Sanitized string safe for filesystem use
    """
    # Replace Windows-invalid characters with dash
    # Invalid chars: < > : " / \ | ? * and control characters (0-31)
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '-', name)

    # Replace multiple spaces/dashes with single dash
    sanitized = re.sub(r'[-\s]+', '-', sanitized)

    # Remove leading/trailing dashes and spaces
    sanitized = sanitized.strip('- ')

    # Convert to lowercase for consistency
    sanitized = sanitized.lower()

    # Ensure we have something left (fallback to "asset" if empty)
    if not sanitized:
        sanitized = "asset"

    return sanitized


class MakerAgent(BaseAgent):
    """Generates digital product assets with self-QA validation based on bundle plan"""

    def __init__(self, db_manager: Optional["DatabaseManager"] = None):
        """Initialize MakerAgent with base functionality"""
        super().__init__("asset_maker", db_manager=db_manager)

    def execute(
        self,
        bundle_id: str,
        emit: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """
        Execute asset generation step with OpenAI

        Args:
            bundle_id: Bundle identifier to load plan from database
            emit: Callback function for progress updates

        Returns:
            Structured maker output data with assets and QA report

        Raises:
            ValueError: If API returns None, invalid response, or bundle not found
            json.JSONDecodeError: If response is not valid JSON
        """
        emit({"event": "log", "step": self.step_name, "message": "Starting asset generation..."})

        try:
            # Load bundle data and planner output
            bundle_data, planner_output = self._load_bundle_data(bundle_id, emit)

            # Get assets array from planner output
            assets = planner_output.get("assets", [])
            if not assets:
                raise ValueError("Bundle plan has no assets to generate")

            total_assets = len(assets)
            emit({"event": "log", "step": self.step_name, "message": f"Generating {total_assets} asset(s)..."})

            # Create base output directory
            from app.settings import settings
            bundle_dir = settings.get_bundle_dir(bundle_id)
            base_output_dir = bundle_dir / "maker_output"
            base_output_dir.mkdir(parents=True, exist_ok=True)

            all_generated_files = []

            # Loop through each asset
            for idx, asset in enumerate(assets, 1):
                asset_name = asset.get("name", f"asset-{idx}")
                asset_id = asset.get("asset_id", f"asset-{idx:03d}")

                # Create subdirectory for this asset
                # Format: asset-001-weekly-planner
                # Use sanitization to remove Windows-invalid characters (: / \ etc)
                safe_asset_name = sanitize_filename(asset_name)
                asset_dir = base_output_dir / f"{asset_id}-{safe_asset_name}"
                asset_dir.mkdir(parents=True, exist_ok=True)

                emit({
                    "event": "log",
                    "step": self.step_name,
                    "message": f"Creating asset {idx}/{total_assets}: {asset_name}..."
                })

                container_name = f"{asset_name}-container-{idx:04d}"

                container = self.client.containers.create(
                    name=container_name,
                    expires_after={
                        "anchor": "last_active_at",
                        "minutes": 20
                    }
                )

                # Build focused prompt for THIS asset only
                asset_prompt = self._build_asset_prompt(bundle_id, planner_output, asset)

                emit({"event": "log", "step": self.step_name, "message": f"Calling OpenAI API for {asset_name}..."})

                # Call OpenAI API for single asset with automatic retry logic
                response = self._call_openai_no_stream_with_retry(
                    emit=emit,
                    model="gpt-5",
                    instructions=self.instructions,
                    input=asset_prompt,
                    tools=[
                        {
                            "type": "code_interpreter",
                            "container": container.id
                        }
                    ],
                    tool_choice="required"
                )

                emit({"event": "log", "step": self.step_name, "message": f"Processing response for {asset_name}..."})

                # Check response status
                if response.status != "completed":
                    error_msg = f"Response status: {response.status} for {asset_name}"
                    self.logger.error(error_msg)
                    emit({"event": "error", "step": self.step_name, "message": error_msg})
                    continue  # Skip to next asset

                # Get list of files from container
                files = self.client.containers.files.list(container_id=container.id)

                # Convert to list for length check
                files_list = list(files.data) if files and hasattr(files, 'data') else []

                if not files_list:
                    emit({
                        "event": "log",
                        "step": self.step_name,
                        "message": f"⚠ No files generated for {asset_name}"
                    })
                else:
                    emit({
                        "event": "log",
                        "step": self.step_name,
                        "message": f"Downloading {len(files_list)} file(s) for {asset_name}..."
                    })
                    downloaded = self._download_files(files=files_list, container_id=container.id, output_dir=asset_dir, emit=emit)
                    all_generated_files.extend(downloaded)

                emit({
                    "event": "log",
                    "step": self.step_name,
                    "message": f"✓ Completed asset {idx}/{total_assets}"
                })

                # Update progress percentage
                progress = int((idx / total_assets) * 100)
                emit({"event": "progress", "step": self.step_name, "pct": progress})

            emit({
                "event": "log",
                "step": self.step_name,
                "message": f"Asset generation complete - {len(all_generated_files)} file(s) created"
            })

            # Update database to mark bundle as completed
            if self.db_manager:
                emit({"event": "log", "step": self.step_name, "message": "Updating bundle status..."})
                save_success = self._save_result(bundle_id)

                if save_success:
                    emit({"event": "log", "step": self.step_name, "message": "Bundle status updated"})
                else:
                    error_msg = "Failed to update bundle status"
                    self.logger.error(error_msg)
                    emit({"event": "error", "step": self.step_name, "message": error_msg})
                    raise ValueError(error_msg)

            # Return simple success status
            return {"status": "completed", "bundle_id": bundle_id}

        except Exception as e:
            # Retry logic is handled by _call_openai_no_stream_with_retry in base class
            # This exception handler catches non-retryable errors or retry exhaustion
            error_message = str(e)

            self.logger.error(f"Execution failed: {error_message}")
            # Error event already emitted by retry logic if applicable
            if "after" not in error_message and "retries" not in error_message:
                emit({"event": "error", "step": self.step_name, "message": error_message})
            raise ValueError(error_message) from e

    def _load_bundle_data(
        self,
        bundle_id: str,
        emit: Callable[[Dict[str, Any]], None]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load bundle data and planner output from database

        Args:
            bundle_id: Bundle identifier
            emit: Callback for progress updates

        Returns:
            Tuple of (bundle_data, planner_output)

        Raises:
            ValueError: If bundle not found or has no planner output
        """
        if not self.db_manager:
            raise ValueError("Cannot load bundle by ID: no db_manager provided")

        emit({"event": "log", "step": self.step_name, "message": f"Loading bundle: {bundle_id}"})

        bundle_record = self.bundle_queries.get_by_id(bundle_id)
        if not bundle_record:
            raise ValueError(f"Bundle not found: {bundle_id}")

        # Parse the planner output JSON
        if not bundle_record.planner_output:
            raise ValueError(f"Bundle {bundle_id} has no planner output")

        try:
            planner_output = json.loads(bundle_record.planner_output)
            self.logger.info(f"Loaded bundle plan for: {planner_output.get('title', 'Unknown')}")
            return bundle_record.model_dump(), planner_output
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse planner_output for {bundle_id}: {e}")
            raise ValueError(f"Invalid planner_output data for {bundle_id}")

    def _build_asset_prompt(
        self,
        bundle_id: str,
        planner_output: Dict[str, Any],
        asset: Dict[str, Any]
    ) -> str:
        """
        Build prompt focused on creating a single asset

        Includes full bundle context for consistency, but focuses on one asset only.

        Args:
            bundle_id: Bundle identifier
            planner_output: Complete planner output from database
            asset: Single asset specification to create

        Returns:
            JSON string with bundle context and focused asset spec
        """
        # Load the base input JSON
        input_data = json.loads(self.input)

        # Inject bundle context (for consistency across all assets)
        input_data["bundle_id"] = bundle_id
        input_data["bundle_context"] = {
            "title": planner_output.get("title"),
            "niche": planner_output.get("niche"),
            "sub_niche": planner_output.get("sub_niche"),
            "target_persona": planner_output.get("target_persona"),
            "brand_voice": planner_output.get("brand_voice"),
            "content_guidelines": planner_output.get("content_guidelines")
        }

        # Focus on THIS asset only
        input_data["asset_to_create"] = asset

        return json.dumps(input_data, indent=2)

    def _extract_file_annotations(self, response) -> list[Dict[str, Any]]:
        """
        Extract file annotations from OpenAI response output

        Args:
            output: Response output object

        Returns:
            List of dicts with file_id, filename, container_id
        """
        file_annotations = []
        for output in response.output:
            if getattr(output, "type", None) == "message":
                for item in output.content:
                    # Check for annotations
                    if hasattr(item, "annotations") and item.annotations:
                        for ann in item.annotations:
                            if getattr(ann, "type", None) == "container_file_citation":
                                file_annotations.append({
                                    "file_id": ann.file_id,
                                    "filename": ann.filename,
                                    "container_id": ann.container_id
                                })
                                self.logger.info(f"Found file: {ann.filename} (ID: {ann.file_id})")

        return file_annotations

    def _download_files(
        self,
        files: list,
        container_id: str,
        output_dir: Path,
        emit: Callable[[Dict[str, Any]], None]
    ) -> list[Path]:
        """
        Download files from OpenAI container and save to output directory

        Args:
            files: List of FileListResponse objects from container
            container_id: Container ID where files are stored
            output_dir: Directory to save files to
            emit: Callback for progress updates

        Returns:
            List of downloaded file paths
        """
        downloaded_files = []

        for file in files:
            try:
                file_id = file.id
                filename = Path(file.path).name

                emit({
                    "event": "log",
                    "step": self.step_name,
                    "message": f"Downloading {filename}..."
                })

                # Download file content from OpenAI
                file_content = self.client.containers.files.content.retrieve(file_id=file_id, container_id=container_id)

                if file_content is None:
                    raise ValueError(f"Failed to retrieve content for file {file_id}")

                # Save to output directory
                output_path = output_dir / filename
                with open(output_path, "wb") as f:
                    f.write(file_content.read())

                downloaded_files.append(output_path)
                self.logger.info(f"✓ Downloaded: {filename} -> {output_path}")

            except Exception as e:
                # Use safe filename access since it might not be defined if error occurs early
                safe_filename = filename if 'filename' in locals() else f"file_{getattr(file, 'id', 'unknown')}"
                self.logger.error(f"Failed to download {safe_filename}: {e}")
                emit({
                    "event": "log",
                    "step": self.step_name,
                    "message": f"⚠ Failed to download {safe_filename}: {str(e)}"
                })

        return downloaded_files

    def _save_result(self, bundle_id: str) -> bool:
        """
        Update bundle status to mark maker step as completed.

        Args:
            bundle_id: The bundle this output belongs to

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.db_manager:
            self.logger.warning("No db_manager available, skipping database save")
            return False

        try:
            self.logger.info(f"Updating bundle status for: {bundle_id}")

            # Update Bundle to advance to packager step with pending status
            if not self.bundle_queries.update_step(bundle_id, "packager", "pending"):
                self.logger.error(f"Failed to update bundle step: {bundle_id}")
                return False

            self.logger.info(f"✓ Bundle step updated: {bundle_id} -> packager (pending)")
            return True

        except Exception as e:
            self.logger.error(f"✗ Critical error in _save_result: {e}", exc_info=True)
            return False
