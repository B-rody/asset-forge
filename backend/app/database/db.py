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

            # ============================================
            # ACTIVE INVENTORY (Work in Progress)
            # ============================================

            # Active idea pool (not yet used for bundles)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ideas (
                    idea_id TEXT PRIMARY KEY,
                    research_session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,

                    title TEXT NOT NULL,
                    niche TEXT NOT NULL,
                    sub_niche TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    roi_estimate REAL NOT NULL,

                    idea_json TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ideas_priority
                ON ideas(priority, roi_estimate DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ideas_created
                ON ideas(created_at DESC)
            """)

            # Active bundles being produced
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bundles (
                    bundle_id TEXT PRIMARY KEY,
                    idea_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    current_step TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,

                    planner_output TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bundles_status
                ON bundles(status, current_step)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bundles_idea
                ON bundles(idea_id)
            """)

            # Maker outputs (tracks created assets on disk)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maker_outputs (
                    maker_id TEXT PRIMARY KEY,
                    bundle_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,

                    output_dir TEXT NOT NULL,
                    maker_output TEXT NOT NULL,

                    is_packaged INTEGER DEFAULT 0,
                    packaged_at TEXT,

                    FOREIGN KEY (bundle_id) REFERENCES bundles(bundle_id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_maker_bundle
                ON maker_outputs(bundle_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_maker_unpackaged
                ON maker_outputs(is_packaged) WHERE is_packaged = 0
            """)

            # ============================================
            # ARCHIVE (Completed Work)
            # ============================================

            # Used ideas (consumed by bundles)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS used_ideas (
                    idea_id TEXT PRIMARY KEY,
                    research_session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    used_at TEXT NOT NULL,
                    bundle_id TEXT NOT NULL,

                    title TEXT NOT NULL,
                    niche TEXT NOT NULL,
                    sub_niche TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    roi_estimate REAL NOT NULL,
                    idea_json TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_used_ideas_title
                ON used_ideas(title)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_used_ideas_created
                ON used_ideas(created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_used_ideas_bundle
                ON used_ideas(bundle_id)
            """)

            # Completed bundles (ready to sell)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS created_bundles (
                    bundle_id TEXT PRIMARY KEY,
                    idea_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,

                    planner_output TEXT NOT NULL,
                    maker_output TEXT NOT NULL,
                    packager_output TEXT NOT NULL,

                    title TEXT NOT NULL,
                    niche TEXT NOT NULL,
                    output_path TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_bundles_completed
                ON created_bundles(completed_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_bundles_niche
                ON created_bundles(niche)
            """)

            # ============================================
            # METADATA (Optional lightweight tracking)
            # ============================================

            # Research session tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    idea_count INTEGER NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_research_created
                ON research_sessions(created_at DESC)
            """)

            # Activity log (tracks all pipeline activities)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    activity_id TEXT PRIMARY KEY,
                    activity_type TEXT NOT NULL,
                    bundle_id TEXT,
                    idea_id TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    duration_seconds INTEGER,
                    error_message TEXT,
                    metadata_json TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_type
                ON activity_log(activity_type, completed_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_bundle
                ON activity_log(bundle_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_completed
                ON activity_log(completed_at DESC)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False  # Allow cross-thread access for async/thread pool usage
            )
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
