"""
Logging configuration for AssetForge backend
"""

import logging
import sys
from rich.logging import RichHandler
from rich.console import Console

def setup_logger(name: str) -> logging.Logger:
    """Set up logger with rich formatting"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Use RichHandler with stderr console to avoid mixing with JSON-Lines IPC on stdout
        stderr_console = Console(stderr=True)
        handler = RichHandler(
            console=stderr_console,
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
        )

        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger
