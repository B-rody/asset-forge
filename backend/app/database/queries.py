"""
Database queries for bundle history
"""

import sqlite3
from typing import List, Optional, Dict, Any
from app.database.db import DatabaseManager
from app.database.models import BundleRecord
from app.logger import setup_logger

logger = setup_logger(__name__)


class BundleQueries:
    """CRUD operations for bundle records"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, bundle: BundleRecord) -> bool:
        """Insert new bundle record"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO bundles (id, timestamp, mode, status, model, output_path, keywords, qa_score, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bundle.id,
                bundle.timestamp,
                bundle.mode,
                bundle.status,
                bundle.model,
                bundle.output_path,
                bundle.keywords,
                bundle.qa_score,
                bundle.error_message
            ))

            conn.commit()
            logger.info(f"Created bundle record: {bundle.id}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Bundle record already exists: {bundle.id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to create bundle record: {e}", exc_info=True)
            return False

    def get_by_id(self, bundle_id: str) -> Optional[BundleRecord]:
        """Fetch bundle by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM bundles WHERE id = ?", (bundle_id,))
            row = cursor.fetchone()

            if row:
                return BundleRecord(**dict(row))
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch bundle: {e}", exc_info=True)
            return None

    def update_status(self, bundle_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update bundle status"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE bundles
                SET status = ?, error_message = ?
                WHERE id = ?
            """, (status, error_message, bundle_id))

            conn.commit()
            logger.info(f"Updated bundle status: {bundle_id} -> {status}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to update bundle status: {e}", exc_info=True)
            return False

    def update_completion(
        self,
        bundle_id: str,
        output_path: str,
        qa_score: Optional[float] = None
    ) -> bool:
        """Mark bundle as completed with output details"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE bundles
                SET status = 'completed', output_path = ?, qa_score = ?
                WHERE id = ?
            """, (output_path, qa_score, bundle_id))

            conn.commit()
            logger.info(f"Marked bundle as completed: {bundle_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to update bundle completion: {e}", exc_info=True)
            return False

    def get_all(self, limit: int = 100) -> List[BundleRecord]:
        """Fetch all bundles (most recent first)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM bundles
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [BundleRecord(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch bundles: {e}", exc_info=True)
            return []

    def get_by_status(self, status: str, limit: int = 100) -> List[BundleRecord]:
        """Fetch bundles by status"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM bundles
                WHERE status = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (status, limit))

            rows = cursor.fetchall()
            return [BundleRecord(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch bundles by status: {e}", exc_info=True)
            return []

    def delete(self, bundle_id: str) -> bool:
        """Delete bundle record"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM bundles WHERE id = ?", (bundle_id,))
            conn.commit()

            logger.info(f"Deleted bundle record: {bundle_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to delete bundle: {e}", exc_info=True)
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get bundle statistics"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) as total FROM bundles")
            total = cursor.fetchone()["total"]

            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM bundles
                GROUP BY status
            """)
            by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Average QA score
            cursor.execute("SELECT AVG(qa_score) as avg_qa FROM bundles WHERE qa_score IS NOT NULL")
            avg_qa = cursor.fetchone()["avg_qa"]

            return {
                "total": total,
                "by_status": by_status,
                "avg_qa_score": round(avg_qa, 2) if avg_qa else None
            }

        except sqlite3.Error as e:
            logger.error(f"Failed to get stats: {e}", exc_info=True)
            return {"total": 0, "by_status": {}, "avg_qa_score": None}
