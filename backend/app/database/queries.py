"""
Database queries for AssetForge pipeline
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.database.db import DatabaseManager
from app.database.models import (
    Idea, Bundle, MakerOutput, UsedIdea, CreatedBundle, ResearchSession, ActivityLog
)
from app.logger import setup_logger

logger = setup_logger(__name__)


class ResearchQueries:
    """Query operations for research sessions"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_session(self, session_id: str, idea_count: int) -> bool:
        """Create new research session"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO research_sessions (session_id, created_at, idea_count)
                VALUES (?, ?, ?)
            """, (session_id, datetime.now().isoformat(), idea_count))

            conn.commit()
            logger.info(f"Created research session: {session_id}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Research session already exists: {session_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to create research session: {e}", exc_info=True)
            return False

    def get_all(self, limit: int = 100) -> List[ResearchSession]:
        """Fetch all research sessions (most recent first)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM research_sessions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [ResearchSession(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch research sessions: {e}", exc_info=True)
            return []


class IdeaQueries:
    """Query operations for ideas table (active inventory)"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, idea: Idea) -> bool:
        """Insert new idea"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ideas (
                    idea_id, research_session_id, created_at,
                    title, niche, sub_niche, priority, roi_estimate, idea_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                idea.idea_id, idea.research_session_id, idea.created_at,
                idea.title, idea.niche, idea.sub_niche, idea.priority,
                idea.roi_estimate, idea.idea_json
            ))

            conn.commit()
            logger.info(f"Created idea: {idea.idea_id}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Idea already exists: {idea.idea_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to create idea: {e}", exc_info=True)
            return False

    def get_by_id(self, idea_id: str) -> Optional[Idea]:
        """Fetch idea by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM ideas WHERE idea_id = ?", (idea_id,))
            row = cursor.fetchone()

            if row:
                return Idea(**dict(row))
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch idea: {e}", exc_info=True)
            return None

    def get_available_ideas(self, weeks_back: int = 8, priorities: List[str] = ["A", "B"]) -> List[Idea]:
        """Get fresh unused ideas from recent research"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(weeks=weeks_back)).isoformat()
            priority_placeholders = ','.join('?' for _ in priorities)

            cursor.execute(f"""
                SELECT * FROM ideas
                WHERE created_at > ?
                AND priority IN ({priority_placeholders})
                ORDER BY priority ASC, roi_estimate DESC
            """, (cutoff_date, *priorities))

            rows = cursor.fetchall()
            return [Idea(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch available ideas: {e}", exc_info=True)
            return []

    def get_all(self, limit: int = 100) -> List[Idea]:
        """Fetch all ideas (sorted by ROI)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM ideas
                ORDER BY priority ASC, roi_estimate DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [Idea(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch ideas: {e}", exc_info=True)
            return []

    def get_historical_titles(self, weeks_back: int = 24) -> List[str]:
        """Get historical idea titles for duplicate detection"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(weeks=weeks_back)).isoformat()

            # Check both ideas and used_ideas tables
            cursor.execute("""
                SELECT title FROM ideas WHERE created_at > ?
                UNION
                SELECT title FROM used_ideas WHERE created_at > ?
            """, (cutoff_date, cutoff_date))

            rows = cursor.fetchall()
            return [row["title"] for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch historical titles: {e}", exc_info=True)
            return []

    def delete(self, idea_id: str) -> bool:
        """Delete idea (used when moving to used_ideas)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM ideas WHERE idea_id = ?", (idea_id,))
            conn.commit()

            logger.info(f"Deleted idea: {idea_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to delete idea: {e}", exc_info=True)
            return False

    def cleanup_expired(self, weeks_back: int = 8) -> int:
        """Delete ideas older than specified weeks"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(weeks=weeks_back)).isoformat()

            cursor.execute("DELETE FROM ideas WHERE created_at < ?", (cutoff_date,))
            conn.commit()

            deleted_count = cursor.rowcount
            logger.info(f"Cleaned up {deleted_count} expired ideas")
            return deleted_count

        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup expired ideas: {e}", exc_info=True)
            return 0


class BundleQueries:
    """Query operations for bundles table (active production)"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, bundle: Bundle) -> bool:
        """Insert new bundle"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO bundles (
                    bundle_id, idea_id, created_at, updated_at,
                    current_step, status, error_message, planner_output
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bundle.bundle_id, bundle.idea_id, bundle.created_at, bundle.updated_at,
                bundle.current_step, bundle.status, bundle.error_message, bundle.planner_output
            ))

            conn.commit()
            logger.info(f"Created bundle: {bundle.bundle_id}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Bundle already exists: {bundle.bundle_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to create bundle: {e}", exc_info=True)
            return False

    def get_by_id(self, bundle_id: str) -> Optional[Bundle]:
        """Fetch bundle by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM bundles WHERE bundle_id = ?", (bundle_id,))
            row = cursor.fetchone()

            if row:
                return Bundle(**dict(row))
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch bundle: {e}", exc_info=True)
            return None

    def update_step(
        self,
        bundle_id: str,
        current_step: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Update bundle step and status"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE bundles
                SET current_step = ?, status = ?, error_message = ?, updated_at = ?
                WHERE bundle_id = ?
            """, (current_step, status, error_message, datetime.now().isoformat(), bundle_id))

            conn.commit()
            logger.info(f"Updated bundle step: {bundle_id} -> {current_step} ({status})")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to update bundle step: {e}", exc_info=True)
            return False

    def update_planner_output(self, bundle_id: str, planner_output: str) -> bool:
        """Update planner output"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE bundles
                SET planner_output = ?, updated_at = ?
                WHERE bundle_id = ?
            """, (planner_output, datetime.now().isoformat(), bundle_id))

            conn.commit()
            logger.info(f"Updated planner output for bundle: {bundle_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to update planner output: {e}", exc_info=True)
            return False

    def get_by_step_and_status(self, current_step: str, status: str) -> List[Bundle]:
        """Fetch bundles by step and status (e.g., ready for next step or failed)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM bundles
                WHERE current_step = ? AND status = ?
                ORDER BY updated_at DESC
            """, (current_step, status))

            rows = cursor.fetchall()
            return [Bundle(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch bundles: {e}", exc_info=True)
            return []

    def get_all(self, limit: int = 100) -> List[Bundle]:
        """Fetch all bundles"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM bundles
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [Bundle(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch bundles: {e}", exc_info=True)
            return []

    def get_ready_for_maker(self, limit: int = 100) -> List[Bundle]:
        """Fetch bundles ready for maker (planner completed)"""
        return self.get_by_step_and_status("planner", "completed")

    def get_ready_for_packager(self, limit: int = 100) -> List[Bundle]:
        """Fetch bundles ready for packager (maker completed)"""
        return self.get_by_step_and_status("maker", "completed")

    def delete(self, bundle_id: str) -> bool:
        """Delete bundle (used when moving to created_bundles)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM bundles WHERE bundle_id = ?", (bundle_id,))
            conn.commit()

            logger.info(f"Deleted bundle: {bundle_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to delete bundle: {e}", exc_info=True)
            return False


class MakerQueries:
    """Query operations for maker_outputs table"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, maker: MakerOutput) -> bool:
        """Insert new maker output"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO maker_outputs (
                    maker_id, bundle_id, created_at,
                    output_dir, maker_output, is_packaged, packaged_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                maker.maker_id, maker.bundle_id, maker.created_at,
                maker.output_dir, maker.maker_output,
                1 if maker.is_packaged else 0, maker.packaged_at
            ))

            conn.commit()
            logger.info(f"Created maker output: {maker.maker_id}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Maker output already exists: {maker.maker_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to create maker output: {e}", exc_info=True)
            return False

    def get_by_bundle_id(self, bundle_id: str) -> Optional[MakerOutput]:
        """Fetch maker output by bundle ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM maker_outputs WHERE bundle_id = ?", (bundle_id,))
            row = cursor.fetchone()

            if row:
                row_dict = dict(row)
                row_dict['is_packaged'] = bool(row_dict['is_packaged'])
                return MakerOutput(**row_dict)
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch maker output: {e}", exc_info=True)
            return None

    def mark_packaged(self, bundle_id: str) -> bool:
        """Mark maker output as packaged"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE maker_outputs
                SET is_packaged = 1, packaged_at = ?
                WHERE bundle_id = ?
            """, (datetime.now().isoformat(), bundle_id))

            conn.commit()
            logger.info(f"Marked maker output as packaged: {bundle_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to mark maker output as packaged: {e}", exc_info=True)
            return False

    def cleanup_old_packaged(self, days_back: int = 30) -> int:
        """Delete packaged maker outputs older than specified days"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

            cursor.execute("""
                DELETE FROM maker_outputs
                WHERE is_packaged = 1 AND packaged_at < ?
            """, (cutoff_date,))

            conn.commit()

            deleted_count = cursor.rowcount
            logger.info(f"Cleaned up {deleted_count} old packaged maker outputs")
            return deleted_count

        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old maker outputs: {e}", exc_info=True)
            return 0


class UsedIdeaQueries:
    """Query operations for used_ideas table (archive)"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, used_idea: UsedIdea) -> bool:
        """Insert used idea"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO used_ideas (
                    idea_id, research_session_id, created_at, used_at, bundle_id,
                    title, niche, sub_niche, priority, roi_estimate, idea_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                used_idea.idea_id, used_idea.research_session_id, used_idea.created_at,
                used_idea.used_at, used_idea.bundle_id, used_idea.title, used_idea.niche,
                used_idea.sub_niche, used_idea.priority, used_idea.roi_estimate, used_idea.idea_json
            ))

            conn.commit()
            logger.info(f"Created used idea: {used_idea.idea_id}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Used idea already exists: {used_idea.idea_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to create used idea: {e}", exc_info=True)
            return False

    def get_all(self, limit: int = 100) -> List[UsedIdea]:
        """Fetch all used ideas (most recent first)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM used_ideas
                ORDER BY used_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [UsedIdea(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch used ideas: {e}", exc_info=True)
            return []


class CreatedBundleQueries:
    """Query operations for created_bundles table (archive)"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, bundle: CreatedBundle) -> bool:
        """Insert created bundle"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO created_bundles (
                    bundle_id, idea_id, created_at, completed_at,
                    planner_output, maker_output, packager_output,
                    title, niche, output_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bundle.bundle_id, bundle.idea_id, bundle.created_at, bundle.completed_at,
                bundle.planner_output, bundle.maker_output, bundle.packager_output,
                bundle.title, bundle.niche, bundle.output_path
            ))

            conn.commit()
            logger.info(f"Created bundle archive: {bundle.bundle_id}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Created bundle already exists: {bundle.bundle_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to create bundle archive: {e}", exc_info=True)
            return False

    def get_by_id(self, bundle_id: str) -> Optional[CreatedBundle]:
        """Fetch created bundle by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM created_bundles WHERE bundle_id = ?", (bundle_id,))
            row = cursor.fetchone()

            if row:
                return CreatedBundle(**dict(row))
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch created bundle: {e}", exc_info=True)
            return None

    def get_all(self, limit: int = 100) -> List[CreatedBundle]:
        """Fetch all created bundles (most recent first)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM created_bundles
                ORDER BY completed_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [CreatedBundle(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch created bundles: {e}", exc_info=True)
            return []

    def get_by_niche(self, niche: str, limit: int = 100) -> List[CreatedBundle]:
        """Fetch created bundles by niche"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM created_bundles
                WHERE niche = ?
                ORDER BY completed_at DESC
                LIMIT ?
            """, (niche, limit))

            rows = cursor.fetchall()
            return [CreatedBundle(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch bundles by niche: {e}", exc_info=True)
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get created bundle statistics"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) as total FROM created_bundles")
            total = cursor.fetchone()["total"]

            # Count by niche
            cursor.execute("""
                SELECT niche, COUNT(*) as count
                FROM created_bundles
                GROUP BY niche
                ORDER BY count DESC
            """)
            by_niche = {row["niche"]: row["count"] for row in cursor.fetchall()}

            return {
                "total": total,
                "by_niche": by_niche
            }

        except sqlite3.Error as e:
            logger.error(f"Failed to get created bundle stats: {e}", exc_info=True)
            return {"total": 0, "by_niche": {}}

    def delete(self, bundle_id: str) -> bool:
        """Delete created bundle from archive"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM created_bundles WHERE bundle_id = ?", (bundle_id,))
            conn.commit()

            logger.info(f"Deleted created bundle: {bundle_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to delete created bundle: {e}", exc_info=True)
            return False


class ActivityLogQueries:
    """Query operations for activity_log table (pipeline activity tracking)"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, activity: ActivityLog) -> bool:
        """Insert new activity log entry"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO activity_log (
                    activity_id, activity_type, bundle_id, idea_id,
                    started_at, completed_at, status, duration_seconds,
                    error_message, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                activity.activity_id, activity.activity_type, activity.bundle_id, activity.idea_id,
                activity.started_at, activity.completed_at, activity.status, activity.duration_seconds,
                activity.error_message, activity.metadata_json
            ))

            conn.commit()
            logger.info(f"Created activity log: {activity.activity_id} ({activity.activity_type})")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Activity log already exists: {activity.activity_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to create activity log: {e}", exc_info=True)
            return False

    def update_completion(
        self,
        activity_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Update activity completion status"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get the start time to calculate duration
            cursor.execute("SELECT started_at FROM activity_log WHERE activity_id = ?", (activity_id,))
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Activity not found for update: {activity_id}")
                return False

            started_at = datetime.fromisoformat(row["started_at"])
            completed_at = datetime.now()
            duration_seconds = int((completed_at - started_at).total_seconds())

            cursor.execute("""
                UPDATE activity_log
                SET status = ?, completed_at = ?, duration_seconds = ?, error_message = ?
                WHERE activity_id = ?
            """, (status, completed_at.isoformat(), duration_seconds, error_message, activity_id))

            conn.commit()
            logger.info(f"Updated activity log: {activity_id} -> {status} ({duration_seconds}s)")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to update activity log: {e}", exc_info=True)
            return False

    def get_all(self, limit: int = 100) -> List[ActivityLog]:
        """Fetch all activity logs (most recent first)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM activity_log
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [ActivityLog(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch activity logs: {e}", exc_info=True)
            return []

    def get_by_type(self, activity_type: str, limit: int = 100) -> List[ActivityLog]:
        """Fetch activity logs by type"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM activity_log
                WHERE activity_type = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (activity_type, limit))

            rows = cursor.fetchall()
            return [ActivityLog(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch activity logs by type: {e}", exc_info=True)
            return []

    def get_by_bundle(self, bundle_id: str) -> List[ActivityLog]:
        """Fetch all activity logs for a specific bundle"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM activity_log
                WHERE bundle_id = ?
                ORDER BY started_at ASC
            """, (bundle_id,))

            rows = cursor.fetchall()
            return [ActivityLog(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch activity logs for bundle: {e}", exc_info=True)
            return []

    def get_recent_activity(self, days: int = 30, limit: int = 100) -> List[ActivityLog]:
        """Get recent pipeline activities"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute("""
                SELECT * FROM activity_log
                WHERE started_at > ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (cutoff_date, limit))

            rows = cursor.fetchall()
            return [ActivityLog(**dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch recent activity: {e}", exc_info=True)
            return []
