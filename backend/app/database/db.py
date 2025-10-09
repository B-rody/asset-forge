"""
SQLite database manager for bundle history
"""

import sqlite3
from pathlib import Path
from typing import Optional
from app.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """Manages SQLite database connection and schema"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _initialize_db(self):
        """Create database and tables if they don't exist"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Create bundles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bundles (
                    id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    model TEXT,
                    output_path TEXT,
                    keywords TEXT,
                    qa_score REAL,
                    error_message TEXT
                )
            """)

            # Create index on timestamp for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bundles_timestamp
                ON bundles(timestamp DESC)
            """)

            # Create index on status
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bundles_status
                ON bundles(status)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row  # Enable column access by name
        return self._conn

    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
