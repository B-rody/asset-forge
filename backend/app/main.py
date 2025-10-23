"""
AssetForge Backend - Main Entry Point
Stdio-based JSON-Lines IPC server
"""

import sys
import asyncio

# Add verbose startup logging to catch import errors
def startup_diagnostic():
    """Log startup diagnostics to stderr for debugging"""
    print("=== AssetForge Backend Startup Diagnostics ===", file=sys.stderr)
    print(f"Python version: {sys.version}", file=sys.stderr)
    print(f"Executable: {sys.executable}", file=sys.stderr)
    print("Attempting imports...", file=sys.stderr)

    try:
        print("  - Importing app.logger...", file=sys.stderr)
        from app.logger import setup_logger
        print("  ✓ app.logger imported", file=sys.stderr)

        print("  - Importing app.ipc...", file=sys.stderr)
        from app.ipc import IPCServer
        print("  ✓ app.ipc imported", file=sys.stderr)

        print("All critical imports successful!", file=sys.stderr)
        print("===========================================", file=sys.stderr)

        return setup_logger, IPCServer
    except Exception as e:
        print(f"❌ FATAL IMPORT ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

# Run diagnostics before main imports
setup_logger, IPCServer = startup_diagnostic()

logger = setup_logger(__name__)


async def main():
    """Main entry point for the backend"""
    try:
        logger.info("AssetForge Backend starting...")

        # Initialize IPC server (orchestrator will be set based on mock mode)
        ipc = IPCServer()

        # Start IPC loop
        await ipc.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ASYNCIO RUN FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
