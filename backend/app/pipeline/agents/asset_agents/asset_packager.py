"""
Packager Agent
Combines all assets and metadata into a ready-to-publish bundle
"""

import json
import subprocess
import shutil
import sys
from typing import Dict, Any, Callable, Optional, TYPE_CHECKING
from datetime import datetime
from pathlib import Path
from app.pipeline.agents.base_agent import BaseAgent

if TYPE_CHECKING:
    from app.database.db import DatabaseManager


class PackagerAgent(BaseAgent):
    """Packages all assets into final deliverable bundle with store listings"""

    def __init__(self, db_manager: Optional["DatabaseManager"] = None):
        """Initialize PackagerAgent with base functionality"""
        super().__init__("asset_packager", db_manager=db_manager)

    def _get_pandoc_path(self) -> str:
        """
        Get path to bundled pandoc executable

        Returns path to bundled pandoc in backend/bin/, or falls back to system pandoc
        Handles both dev mode (running from source) and production mode (compiled with Nuitka)

        Returns:
            str: Path to pandoc executable
        """
        # Determine base path based on whether we're running as compiled binary or source
        if getattr(sys, 'frozen', False):
            # Running as compiled binary (Nuitka)
            base_path = Path(sys.executable).parent
        else:
            # Running in dev mode - navigate from backend/app/pipeline/agents/ to backend/
            base_path = Path(__file__).parent.parent.parent.parent

        # Platform-specific executable name
        if sys.platform == 'win32':
            pandoc_exe = base_path / 'bin' / 'pandoc.exe'
        elif sys.platform == 'darwin':
            pandoc_exe = base_path / 'bin' / 'pandoc'
        else:
            pandoc_exe = base_path / 'bin' / 'pandoc'

        # Use bundled pandoc if it exists, otherwise fallback to system pandoc
        if pandoc_exe.exists():
            self.logger.info(f"Using bundled pandoc: {pandoc_exe}")
            return str(pandoc_exe)
        else:
            self.logger.warning(f"Bundled pandoc not found at {pandoc_exe}, using system pandoc")
            return 'pandoc'

    def execute(
        self,
        bundle_id: str,
        emit: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """
        Execute packaging step to create final bundle

        Args:
            bundle_id: Bundle identifier to load data from database
            emit: Callback function for progress updates

        Returns:
            Dict with store_title, store_description, and file paths

        Raises:
            ValueError: If bundle not found or missing required data
        """
        emit({"event": "log", "step": self.step_name, "message": "Starting bundle packaging..."})
        emit({"event": "progress", "step": self.step_name})

        try:
            # Load bundle data and planner output
            bundle_data, planner_output = self._load_bundle_data(bundle_id, emit)

            emit({"event": "progress", "step": self.step_name})

            # Get bundle directory
            from app.settings import settings
            bundle_dir = settings.get_bundle_dir(bundle_id)
            maker_output_dir = bundle_dir / "maker_output"

            if not maker_output_dir.exists():
                raise ValueError(f"No maker output found for bundle: {bundle_id}")

            # Collect all asset metadata
            emit({"event": "log", "step": self.step_name, "message": "Collecting asset metadata..."})
            assets_metadata = self._collect_asset_metadata(maker_output_dir, emit)

            emit({"event": "progress", "step": self.step_name})

            # Build prompt for store listing generation
            emit({"event": "log", "step": self.step_name, "message": "Generating store listings..."})
            prompt = self._build_prompt(bundle_id, planner_output, assets_metadata)

            # Call OpenAI API to generate store listings with structured output
            emit({"event": "log", "step": self.step_name, "message": "Calling OpenAI API..."})

            response = self.client.responses.create(
                model="gpt-5",
                instructions=self.instructions,
                input=prompt,
                stream=True,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "packager_response",
                        "schema": self.output_schema,
                        "strict": True
                    }
                }
            )

            # Handle streaming response
            emit({"event": "log", "step": self.step_name, "message": "Processing stream..."})
            result = self._handle_stream(response, emit)

            # Validate against schema
            emit({"event": "log", "step": self.step_name, "message": "Validating response..."})
            if not self._validate_response(result):
                raise ValueError("Response validation failed against schema")

            # Extract store listing data from structured response
            emit({"event": "log", "step": self.step_name, "message": "Store listings generated"})
            store_title = result.get("store_title", "")
            store_description = result.get("store_description", "")

            # Convert markdown files to PDF using pandoc
            emit({"event": "log", "step": self.step_name, "message": "Converting markdown files to PDF..."})
            converted_pdfs = self._convert_markdown_to_pdf(maker_output_dir, emit)

            emit({"event": "progress", "step": self.step_name})

            # Save bundle metadata as markdown file
            emit({"event": "log", "step": self.step_name, "message": "Creating bundle metadata..."})
            metadata_path = self._save_bundle_metadata(
                bundle_dir=bundle_dir,
                bundle_title=planner_output.get("title", "Untitled Bundle"),
                bundle_niche=planner_output.get("niche", "Unknown"),
                store_title=store_title,
                store_description=store_description,
                assets_metadata=assets_metadata,
                converted_pdfs=converted_pdfs
            )

            # Copy final bundle to user's output directory
            emit({"event": "log", "step": self.step_name, "message": "Creating final bundle..."})
            final_output_path = self._copy_final_bundle(
                maker_output_dir=maker_output_dir,
                bundle_dir=bundle_dir,
                bundle_id=bundle_id,
                emit=emit
            )

            emit({"event": "progress", "step": self.step_name})

            # Update database to mark packager step as completed
            emit({"event": "log", "step": self.step_name, "message": "Updating bundle status..."})
            save_success = self._save_result(bundle_id)

            if not save_success:
                error_msg = "Failed to update bundle status"
                self.logger.error(error_msg)
                emit({"event": "error", "step": self.step_name, "message": error_msg})
                raise ValueError(error_msg)

            emit({"event": "progress", "step": self.step_name})
            emit({"event": "log", "step": self.step_name, "message": "Bundle packaging complete"})

            # Return final metadata
            return {
                "status": "completed",
                "bundle_id": bundle_id,
                "store_title": store_title,
                "store_description": store_description,
                "metadata_file": str(metadata_path),
                "converted_pdfs": [str(p) for p in converted_pdfs],
                "final_output_path": str(final_output_path)
            }

        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            raise

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

    def _collect_asset_metadata(
        self,
        maker_output_dir: Path,
        emit: Callable[[Dict[str, Any]], None]
    ) -> list[Dict[str, Any]]:
        """
        Scan maker_output directory for all asset_metadata.json files

        Args:
            maker_output_dir: Directory containing maker output with subdirectories
            emit: Callback for progress updates

        Returns:
            List of asset metadata dicts with {name, description, format}
        """
        assets_metadata = []

        # Find all asset_metadata.json files in subdirectories
        metadata_files = list(maker_output_dir.rglob("asset_metadata.json"))

        if not metadata_files:
            self.logger.warning("No asset_metadata.json files found in maker_output")
            emit({"event": "log", "step": self.step_name, "message": "⚠ No asset metadata files found"})
            return []

        emit({"event": "log", "step": self.step_name, "message": f"Found {len(metadata_files)} asset(s)"})

        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    assets_metadata.append({
                        "name": metadata.get("name", "Unknown"),
                        "description": metadata.get("description", ""),
                        "format": metadata.get("format", "Unknown")
                    })
                    self.logger.info(f"Loaded metadata: {metadata.get('name')}")
            except Exception as e:
                self.logger.error(f"Failed to read {metadata_file}: {e}")
                emit({"event": "log", "step": self.step_name, "message": f"⚠ Failed to read {metadata_file.name}"})

        return assets_metadata

    def _build_prompt(
        self,
        bundle_id: str,
        planner_output: Dict[str, Any],
        assets_metadata: list[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for store listing generation

        Args:
            bundle_id: Bundle identifier
            planner_output: Complete planner output from database
            assets_metadata: List of asset metadata dicts

        Returns:
            JSON string with bundle info and assets
        """
        # Load the base input JSON
        input_data = json.loads(self.input)

        # Inject bundle information
        input_data["bundle_id"] = bundle_id
        input_data["bundle_info"] = {
            "title": planner_output.get("title", "Untitled Bundle"),
            "description": planner_output.get("one_liner", planner_output.get("description", "")),
            "niche": planner_output.get("niche", ""),
            "sub_niche": planner_output.get("sub_niche", ""),
            "target_persona": planner_output.get("target_persona", {})
        }

        # Add assets metadata
        input_data["assets"] = assets_metadata

        return json.dumps(input_data, indent=2)

    def _convert_markdown_to_pdf(
        self,
        maker_output_dir: Path,
        emit: Callable[[Dict[str, Any]], None]
    ) -> list[Path]:
        """
        Convert all CONVERTPDF_*.md files to PDF using pandoc

        Args:
            maker_output_dir: Directory containing maker output subdirectories
            emit: Callback for progress updates

        Returns:
            List of converted PDF file paths
        """
        converted_pdfs = []

        # Find all CONVERTPDF_*.md files
        markdown_files = list(maker_output_dir.rglob("CONVERTPDF_*.md"))

        if not markdown_files:
            self.logger.info("No markdown files to convert")
            return []

        emit({"event": "log", "step": self.step_name, "message": f"Converting {len(markdown_files)} markdown file(s) to PDF..."})

        # Get path to bundled pandoc executable
        pandoc_path = self._get_pandoc_path()

        for md_file in markdown_files:
            try:
                # Remove CONVERTPDF_ prefix from filename
                pdf_name = md_file.name.replace("CONVERTPDF_", "").replace(".md", ".pdf")
                pdf_path = md_file.parent / pdf_name

                # Run pandoc to convert markdown to PDF
                result = subprocess.run(
                    [
                        pandoc_path,
                        str(md_file),
                        "-o",
                        str(pdf_path),
                        "--pdf-engine=xelatex"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    converted_pdfs.append(pdf_path)
                    self.logger.info(f"✓ Converted: {md_file.name} -> {pdf_name}")
                    emit({"event": "log", "step": self.step_name, "message": f"✓ Converted {pdf_name}"})

                    # Optionally delete the markdown file after conversion
                    # md_file.unlink()
                else:
                    error_msg = f"Pandoc failed for {md_file.name}: {result.stderr}"
                    self.logger.error(error_msg)
                    emit({"event": "log", "step": self.step_name, "message": f"⚠ {error_msg}"})

            except subprocess.TimeoutExpired:
                self.logger.error(f"Pandoc timeout for {md_file.name}")
                emit({"event": "log", "step": self.step_name, "message": f"⚠ Timeout converting {md_file.name}"})
            except Exception as e:
                self.logger.error(f"Failed to convert {md_file.name}: {e}")
                emit({"event": "log", "step": self.step_name, "message": f"⚠ Failed to convert {md_file.name}"})

        return converted_pdfs

    def _save_bundle_metadata(
        self,
        bundle_dir: Path,
        bundle_title: str,
        bundle_niche: str,
        store_title: str,
        store_description: str,
        assets_metadata: list[Dict[str, Any]],
        converted_pdfs: list[Path]
    ) -> Path:
        """
        Save bundle metadata as human-readable markdown file in bundle root

        Args:
            bundle_dir: Bundle root directory
            bundle_title: Internal bundle title
            bundle_niche: Bundle niche
            store_title: Generated store listing title
            store_description: Generated store listing description
            assets_metadata: List of asset metadata dicts
            converted_pdfs: List of converted PDF paths

        Returns:
            Path to created bundle_metadata.md file
        """
        metadata_path = bundle_dir / "bundle_metadata.md"

        # Build metadata content
        content = f"""# {bundle_title}

**Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Niche**: {bundle_niche}

---

## Store Listing

### Title
{store_title}

### Description
{store_description}

---

## Assets Included

"""

        # Add asset list
        for idx, asset in enumerate(assets_metadata, 1):
            content += f"{idx}. **{asset['name']}** ({asset['format']})\n"
            content += f"   {asset['description']}\n\n"

        # Add converted PDFs section
        if converted_pdfs:
            content += "## Converted PDFs\n\n"
            for pdf_path in converted_pdfs:
                content += f"- {pdf_path.name}\n"
            content += "\n"

        # Write to file
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info(f"✓ Created bundle metadata: {metadata_path}")
        return metadata_path

    def _copy_final_bundle(
        self,
        maker_output_dir: Path,
        bundle_dir: Path,
        bundle_id: str,
        emit: Callable[[Dict[str, Any]], None]
    ) -> Path:
        """
        Copy final bundle structure to user's output directory

        Creates a clean bundle with:
        - Asset subdirectories (without internal asset_metadata.json files)
        - bundle_metadata.md in root
        - Converted PDFs where applicable

        Args:
            maker_output_dir: Internal maker output directory with all assets
            bundle_dir: Internal bundle directory containing bundle_metadata.md
            bundle_id: Bundle identifier for creating output subdirectory
            emit: Callback for progress updates

        Returns:
            Path to final output directory in user's configured output_dir
        """
        from app.settings import settings

        # Determine final output location
        if settings.output_dir:
            final_output_dir = settings.output_dir / bundle_id
        else:
            # Fallback to default output directory if not configured
            final_output_dir = settings.data_dir / "output" / bundle_id

        emit({"event": "log", "step": self.step_name, "message": f"Copying bundle to {final_output_dir}..."})

        # Create final output directory
        final_output_dir.mkdir(parents=True, exist_ok=True)

        # Copy asset subdirectories from maker_output
        if maker_output_dir.exists():
            for asset_subdir in maker_output_dir.iterdir():
                if asset_subdir.is_dir():
                    dest_dir = final_output_dir / asset_subdir.name

                    # Copy entire subdirectory
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    shutil.copytree(asset_subdir, dest_dir)

                    # Remove internal asset_metadata.json files from final bundle
                    metadata_file = dest_dir / "asset_metadata.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
                        self.logger.info(f"Removed internal metadata from {dest_dir.name}")

                    # Remove CONVERTPDF_*.md source files from final bundle (keep only converted PDFs)
                    for convertpdf_file in dest_dir.glob("CONVERTPDF_*.md"):
                        convertpdf_file.unlink()
                        self.logger.info(f"Removed conversion source: {convertpdf_file.name}")

        # Copy bundle_metadata.md to final bundle root
        source_metadata = bundle_dir / "bundle_metadata.md"
        if source_metadata.exists():
            dest_metadata = final_output_dir / "bundle_metadata.md"
            shutil.copy2(source_metadata, dest_metadata)
            self.logger.info("Copied bundle_metadata.md to final bundle")

        self.logger.info(f"✓ Final bundle created at: {final_output_dir}")
        emit({"event": "log", "step": self.step_name, "message": f"✓ Bundle ready at {final_output_dir}"})

        return final_output_dir

    def _save_result(self, bundle_id: str) -> bool:
        """
        Update bundle status to mark packager step as completed

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

            # Update Bundle to set current_step="packager" and status="completed"
            if not self.bundle_queries.update_step(bundle_id, "packager", "completed"):
                self.logger.error(f"Failed to update bundle step: {bundle_id}")
                return False

            self.logger.info(f"✓ Bundle step updated: {bundle_id} -> packager (completed)")
            return True

        except Exception as e:
            self.logger.error(f"✗ Critical error in _save_result: {e}", exc_info=True)
            return False
