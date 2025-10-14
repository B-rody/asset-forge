"""
JSON-Lines IPC Communication Layer
Handles stdio-based communication with frontend
"""

import sys
import asyncio
import orjson
from typing import Any, Dict, Optional
from app.logger import setup_logger

logger = setup_logger(__name__)


class IPCServer:
    """JSON-Lines IPC server for stdio communication"""

    def __init__(self):
        self.orchestrator = None  # Will be set based on mock mode
    
    async def run(self):
        """Main IPC loop - read commands from stdin, send events to stdout"""
        logger.info("IPC server started, listening on stdin...")
        
        # Read from stdin line by line
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Read line from stdin (blocking in thread pool to avoid blocking event loop)
                line = await loop.run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    # EOF reached
                    break
                
                # Parse JSON command
                try:
                    command = orjson.loads(line)
                    await self.handle_command(command)
                except orjson.JSONDecodeError as e:
                    self.emit_error(None, f"Invalid JSON: {e}")
            
            except Exception as e:
                logger.error(f"Error in IPC loop: {e}", exc_info=True)
                self.emit_error(None, f"IPC error: {e}")
    
    async def handle_command(self, command: Dict[str, Any]):
        """Handle incoming command from frontend"""
        cmd = command.get("cmd")

        if cmd == "run_pipeline":
            mode = command.get("mode", "one_click")
            params = command.get("params", {})

            # Determine which orchestrator to use based on mockMode
            mock_mode = params.get("mockMode", False)
            self._set_orchestrator(mock_mode)

            await self.orchestrator.run_pipeline(mode, params, self.emit_event)

        elif cmd == "build_from_idea":
            params = command.get("params", {})
            idea_id = params.get("idea_id")

            if not idea_id:
                self.emit_error(None, "No idea_id provided")
                return

            # Use real orchestrator for building from idea
            self._set_orchestrator(False)

            await self.orchestrator.run_from_idea(idea_id, self.emit_event)

        elif cmd == "generate_assets_from_bundle":
            params = command.get("params", {})
            bundle_id = params.get("bundle_id")

            if not bundle_id:
                self.emit_error(None, "No bundle_id provided")
                return

            # Use real orchestrator for generating assets
            self._set_orchestrator(False)

            await self.orchestrator.run_maker_from_bundle(bundle_id, self.emit_event)

        elif cmd == "package_bundle":
            params = command.get("params", {})
            bundle_id = params.get("bundle_id")

            if not bundle_id:
                self.emit_error(None, "No bundle_id provided")
                return

            # Use real orchestrator for packaging
            self._set_orchestrator(False)

            await self.orchestrator.run_packager_from_bundle(bundle_id, self.emit_event)

        elif cmd == "re_run_step":
            params = command.get("params", {})
            bundle_id = params.get("bundle_id")
            step = params.get("step")

            # Use mock orchestrator for re-runs (can be enhanced later)
            self._set_orchestrator(True)

            await self.orchestrator.re_run_step(bundle_id, step, self.emit_event)

        elif cmd == "get_bundle_history":
            params = command.get("params", {})
            limit = params.get("limit", 100)
            bundles = self.orchestrator.bundle_queries.get_all(limit=limit)
            self.emit_event({
                "event": "bundle_history",
                "bundles": [bundle.model_dump() for bundle in bundles],
                "total": len(bundles)
            })

        elif cmd == "get_bundle_details":
            params = command.get("params", {})
            bundle_id = params.get("bundle_id")
            bundle = self.orchestrator.bundle_queries.get_by_id(bundle_id)
            if bundle:
                self.emit_event({
                    "event": "bundle_details",
                    "bundle": bundle.model_dump()
                })
            else:
                self.emit_error(None, f"Bundle not found: {bundle_id}")

        elif cmd == "get_bundle_stats":
            stats = self.orchestrator.bundle_queries.get_stats()
            self.emit_event({
                "event": "bundle_stats",
                "stats": stats
            })

        elif cmd == "save_api_key":
            params = command.get("params", {})
            api_key = params.get("api_key")
            if not api_key:
                self.emit_error(None, "No API key provided")
                return

            from app.security.keyring_store import save_api_key
            success = save_api_key(api_key)
            self.emit_event({
                "event": "api_key_saved",
                "success": success
            })

        elif cmd == "get_api_key":
            from app.security.keyring_store import has_api_key
            has_key = has_api_key()
            self.emit_event({
                "event": "api_key_status",
                "has_key": has_key
            })

        elif cmd == "delete_api_key":
            from app.security.keyring_store import delete_api_key
            success = delete_api_key()
            self.emit_event({
                "event": "api_key_deleted",
                "success": success
            })

        elif cmd == "get_output_folder":
            from app.settings import settings
            # Ensure output folder exists
            settings.output_dir.mkdir(parents=True, exist_ok=True)
            self.emit_event({
                "event": "output_folder_status",
                "current_path": str(settings.output_dir),
                "default_path": str(settings.get_default_output_dir()),
                "is_custom": str(settings.output_dir) != str(settings.get_default_output_dir())
            })

        elif cmd == "save_output_folder":
            params = command.get("params", {})
            folder_path = params.get("folder_path")

            if not folder_path:
                self.emit_error(None, "No folder path provided")
                return

            from pathlib import Path
            from app.config_store import save_preference
            from app.settings import settings

            # Validate path
            try:
                path = Path(folder_path)

                # Check if path exists
                if not path.exists():
                    self.emit_error(None, f"Path does not exist: {folder_path}")
                    return

                # Check if it's a directory
                if not path.is_dir():
                    self.emit_error(None, f"Path is not a directory: {folder_path}")
                    return

                # Check if writable (try to create a test file)
                try:
                    test_file = path / ".assetforge_test"
                    test_file.touch()
                    test_file.unlink()
                except Exception as e:
                    self.emit_error(None, f"Cannot write to directory: {str(e)}")
                    return

                # Save to config
                success = save_preference(settings.config_dir, "output_folder", str(path))

                if success:
                    # Update settings in memory
                    settings.output_dir = path
                    settings.output_dir.mkdir(parents=True, exist_ok=True)

                    self.emit_event({
                        "event": "output_folder_saved",
                        "success": True,
                        "path": str(path)
                    })
                else:
                    self.emit_error(None, "Failed to save output folder preference")

            except Exception as e:
                self.emit_error(None, f"Invalid path: {str(e)}")

        elif cmd == "reset_output_folder":
            from app.config_store import delete_preference
            from app.settings import settings

            # Delete saved preference
            success = delete_preference(settings.config_dir, "output_folder")

            if success:
                # Reset to default in memory
                default_dir = settings.get_default_output_dir()
                settings.output_dir = default_dir
                settings.output_dir.mkdir(parents=True, exist_ok=True)

                self.emit_event({
                    "event": "output_folder_reset",
                    "success": True,
                    "path": str(default_dir)
                })
            else:
                self.emit_error(None, "Failed to reset output folder")

        elif cmd == "get_ideas":
            try:
                logger.info("Handling get_ideas command")

                # Ensure orchestrator is initialized
                self._set_orchestrator(False)
                logger.debug(f"Orchestrator initialized: {type(self.orchestrator).__name__}")

                params = command.get("params", {})
                limit = params.get("limit", 100)

                from app.database.queries import IdeaQueries
                idea_queries = IdeaQueries(self.orchestrator.db_manager)
                logger.debug("IdeaQueries created, fetching ideas...")

                ideas = idea_queries.get_all(limit=limit)
                logger.info(f"Retrieved {len(ideas)} ideas from database")

                # Serialize ideas to dicts
                ideas_data = [idea.model_dump() for idea in ideas]
                logger.debug(f"Serialized {len(ideas_data)} ideas")

                self.emit_event({
                    "event": "ideas_list",
                    "ideas": ideas_data,
                    "total": len(ideas_data)
                })
                logger.info(f"Emitted ideas_list event with {len(ideas_data)} ideas")

            except Exception as e:
                logger.error(f"Failed to get ideas: {e}", exc_info=True)
                self.emit_error(None, f"Failed to retrieve ideas: {str(e)}")

        elif cmd == "get_bundles":
            try:
                logger.info("Handling get_bundles command")

                # Ensure orchestrator is initialized
                self._set_orchestrator(False)

                params = command.get("params", {})
                limit = params.get("limit", 100)

                from app.database.queries import BundleQueries
                bundle_queries = BundleQueries(self.orchestrator.db_manager)
                bundles = bundle_queries.get_all(limit=limit)
                logger.info(f"Retrieved {len(bundles)} bundles from database")

                self.emit_event({
                    "event": "bundles_list",
                    "bundles": [bundle.model_dump() for bundle in bundles],
                    "total": len(bundles)
                })
                logger.info(f"Emitted bundles_list event with {len(bundles)} bundles")

            except Exception as e:
                logger.error(f"Failed to get bundles: {e}", exc_info=True)
                self.emit_error(None, f"Failed to retrieve bundles: {str(e)}")

        elif cmd == "get_ready_bundles":
            try:
                logger.info("Handling get_ready_bundles command")

                # Ensure orchestrator is initialized
                self._set_orchestrator(False)

                params = command.get("params", {})
                limit = params.get("limit", 100)

                from app.database.queries import BundleQueries
                bundle_queries = BundleQueries(self.orchestrator.db_manager)
                bundles = bundle_queries.get_ready_for_maker(limit=limit)
                logger.info(f"Retrieved {len(bundles)} ready bundles from database")

                self.emit_event({
                    "event": "ready_bundles_list",
                    "bundles": [bundle.model_dump() for bundle in bundles],
                    "total": len(bundles)
                })
                logger.info(f"Emitted ready_bundles_list event with {len(bundles)} bundles")

            except Exception as e:
                logger.error(f"Failed to get ready bundles: {e}", exc_info=True)
                self.emit_error(None, f"Failed to retrieve ready bundles: {str(e)}")

        elif cmd == "get_generated_bundles":
            try:
                logger.info("Handling get_generated_bundles command")

                # Ensure orchestrator is initialized
                self._set_orchestrator(False)

                params = command.get("params", {})
                limit = params.get("limit", 100)

                from app.database.queries import BundleQueries
                bundle_queries = BundleQueries(self.orchestrator.db_manager)
                bundles = bundle_queries.get_ready_for_packager(limit=limit)
                logger.info(f"Retrieved {len(bundles)} generated bundles from database")

                self.emit_event({
                    "event": "generated_bundles_list",
                    "bundles": [bundle.model_dump() for bundle in bundles],
                    "total": len(bundles)
                })
                logger.info(f"Emitted generated_bundles_list event with {len(bundles)} bundles")

            except Exception as e:
                logger.error(f"Failed to get generated bundles: {e}", exc_info=True)
                self.emit_error(None, f"Failed to retrieve generated bundles: {str(e)}")

        elif cmd == "get_activity_log":
            try:
                logger.info("Handling get_activity_log command")

                # Ensure orchestrator is initialized
                self._set_orchestrator(False)

                params = command.get("params", {})
                limit = params.get("limit", 100)

                from app.database.queries import ActivityLogQueries
                activity_queries = ActivityLogQueries(self.orchestrator.db_manager)
                activities = activity_queries.get_all(limit=limit)
                logger.info(f"Retrieved {len(activities)} activity logs from database")

                self.emit_event({
                    "event": "activity_log_list",
                    "activities": [activity.model_dump() for activity in activities],
                    "total": len(activities)
                })
                logger.info(f"Emitted activity_log_list event with {len(activities)} activities")

            except Exception as e:
                logger.error(f"Failed to get activity log: {e}", exc_info=True)
                self.emit_error(None, f"Failed to retrieve activity log: {str(e)}")

        elif cmd == "get_library_stats":
            try:
                logger.info("Handling get_library_stats command")

                # Ensure orchestrator is initialized
                self._set_orchestrator(False)

                from app.database.queries import IdeaQueries, BundleQueries
                idea_queries = IdeaQueries(self.orchestrator.db_manager)
                bundle_queries = BundleQueries(self.orchestrator.db_manager)

                ideas = idea_queries.get_all(limit=1000)
                bundles = bundle_queries.get_all(limit=1000)
                logger.info(f"Retrieved stats: {len(ideas)} ideas, {len(bundles)} bundles")

                self.emit_event({
                    "event": "library_stats",
                    "stats": {
                        "ideas_count": len(ideas),
                        "bundles_count": len(bundles)
                    }
                })
                logger.info(f"Emitted library_stats event")

            except Exception as e:
                logger.error(f"Failed to get library stats: {e}", exc_info=True)
                self.emit_error(None, f"Failed to retrieve library stats: {str(e)}")

        elif cmd == "get_research_sessions":
            try:
                logger.info("Handling get_research_sessions command")

                # Ensure orchestrator is initialized
                self._set_orchestrator(False)

                params = command.get("params", {})
                limit = params.get("limit", 100)

                from app.database.queries import ResearchQueries
                research_queries = ResearchQueries(self.orchestrator.db_manager)
                sessions = research_queries.get_all(limit=limit)
                logger.info(f"Retrieved {len(sessions)} research sessions from database")

                self.emit_event({
                    "event": "research_sessions_list",
                    "sessions": [session.model_dump() for session in sessions],
                    "total": len(sessions)
                })
                logger.info(f"Emitted research_sessions_list event with {len(sessions)} sessions")

            except Exception as e:
                logger.error(f"Failed to get research sessions: {e}", exc_info=True)
                self.emit_error(None, f"Failed to retrieve research sessions: {str(e)}")

        elif cmd == "get_created_bundles":
            try:
                logger.info("Handling get_created_bundles command")

                # Ensure orchestrator is initialized
                self._set_orchestrator(False)

                params = command.get("params", {})
                limit = params.get("limit", 100)

                from app.database.queries import CreatedBundleQueries
                created_bundle_queries = CreatedBundleQueries(self.orchestrator.db_manager)
                bundles = created_bundle_queries.get_all(limit=limit)
                logger.info(f"Retrieved {len(bundles)} completed bundles from database")

                self.emit_event({
                    "event": "completed_bundles_list",
                    "bundles": [bundle.model_dump() for bundle in bundles],
                    "total": len(bundles)
                })
                logger.info(f"Emitted completed_bundles_list event with {len(bundles)} bundles")

            except Exception as e:
                logger.error(f"Failed to get completed bundles: {e}", exc_info=True)
                self.emit_error(None, f"Failed to retrieve completed bundles: {str(e)}")

        elif cmd == "open_folder":
            params = command.get("params", {})
            path = params.get("path")

            if not path:
                self.emit_error(None, "No path provided")
                return

            try:
                import platform
                import subprocess
                from pathlib import Path

                # Convert to Path object and get parent directory
                folder_path = Path(path).parent if Path(path).is_file() else Path(path)

                # Ensure path exists
                if not folder_path.exists():
                    self.emit_error(None, f"Path does not exist: {folder_path}")
                    return

                # Open file explorer based on platform
                system = platform.system()
                if system == "Windows":
                    subprocess.Popen(f'explorer "{folder_path}"')
                elif system == "Darwin":  # macOS
                    subprocess.Popen(["open", str(folder_path)])
                else:  # Linux
                    subprocess.Popen(["xdg-open", str(folder_path)])

                logger.info(f"Opened folder: {folder_path}")
                self.emit_event({
                    "event": "folder_opened",
                    "success": True,
                    "path": str(folder_path)
                })

            except Exception as e:
                logger.error(f"Failed to open folder: {e}", exc_info=True)
                self.emit_error(None, f"Failed to open folder: {str(e)}")

        elif cmd == "reset_database":
            from app.settings import settings
            import os

            try:
                # Close any existing connections
                if self.orchestrator and hasattr(self.orchestrator, 'db_manager'):
                    self.orchestrator.db_manager.close()
                    self.orchestrator = None

                # Delete database file
                if settings.db_path.exists():
                    os.remove(settings.db_path)
                    self.emit_event({
                        "event": "database_reset",
                        "success": True,
                        "message": "Database reset successfully"
                    })
                else:
                    self.emit_error(None, "Database file not found")

            except Exception as e:
                self.emit_error(None, f"Failed to reset database: {e}")

        else:
            self.emit_error(None, f"Unknown command: {cmd}")
    
    def emit_event(self, event: Dict[str, Any]):
        """Emit event to stdout (JSON-Lines format)"""
        try:
            json_bytes = orjson.dumps(event)
            # Write bytes directly to buffer to avoid Windows cp1252 encoding issues
            sys.stdout.buffer.write(json_bytes + b'\n')
            sys.stdout.buffer.flush()
        except Exception as e:
            logger.error(f"Failed to emit event: {e}", exc_info=True)
    
    def emit_error(self, step: str | None, message: str):
        """Emit error event"""
        self.emit_event({
            "event": "error",
            "step": step,
            "message": message
        })

    def _set_orchestrator(self, mock_mode: bool):
        """Set orchestrator based on mock mode"""
        if mock_mode:
            from app.mock import MockPipelineOrchestrator
            if not isinstance(self.orchestrator, MockPipelineOrchestrator):
                logger.info("Switching to MOCK orchestrator")
                self.orchestrator = MockPipelineOrchestrator()
        else:
            from app.pipeline.orchestrator import PipelineOrchestrator
            if not isinstance(self.orchestrator, PipelineOrchestrator):
                logger.info("Switching to REAL orchestrator")
                self.orchestrator = PipelineOrchestrator()
