"""
AssetForge Backend - Main Entry Point
Stdio-based JSON-Lines IPC server
"""

import sys
import asyncio
from app.ipc import IPCServer
from app.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    """Main entry point for the backend"""
    logger.info("AssetForge Backend starting...")

    # Initialize IPC server (orchestrator will be set based on mock mode)
    ipc = IPCServer()

    # Start IPC loop
    try:
        await ipc.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
