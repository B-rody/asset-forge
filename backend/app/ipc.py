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

        else:
            self.emit_error(None, f"Unknown command: {cmd}")
    
    def emit_event(self, event: Dict[str, Any]):
        """Emit event to stdout (JSON-Lines format)"""
        try:
            json_bytes = orjson.dumps(event)
            sys.stdout.write(json_bytes.decode('utf-8') + '\n')
            sys.stdout.flush()
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
