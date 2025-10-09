"""
Logging configuration for AssetForge backend
"""

import logging
import sys
from rich.logging import RichHandler

def setup_logger(name: str) -> logging.Logger:
    """Set up logger with rich formatting"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Use RichHandler for beautiful console output
        # Note: RichHandler defaults to stderr to avoid mixing with IPC on stdout
        handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
        )
        
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger
