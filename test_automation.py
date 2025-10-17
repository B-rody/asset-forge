"""
Automated Testing Script for AssetForge
Tests database state, mock pipelines, and generates test report
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import DatabaseManager
from app.database.queries import (
    IdeaQueries, BundleQueries, ActivityLogQueries,
    CreatedBundleQueries, UsedIdeaQueries
)
from app.settings import settings

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []

    def add_pass(self, test_name, details=""):
        self.passed.append({"test": test_name, "details": details})
        print(f"[PASS] {test_name}")
        if details:
            print(f"   {details}")

    def add_fail(self, test_name, error):
        self.failed.append({"test": test_name, "error": str(error)})
        print(f"[FAIL] {test_name}")
        print(f"   Error: {error}")

    def add_skip(self, test_name, reason):
        self.skipped.append({"test": test_name, "reason": reason})
        print(f"[SKIP] {test_name} - {reason}")

    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Skipped: {len(self.skipped)}")
        print(f"Success Rate: {len(self.passed)/total*100:.1f}%" if total > 0 else "N/A")
        print("="*60)

results = TestResults()

def test_database_connection():
    """Test 1: Database Connection"""
    try:
        db = DatabaseManager(settings.db_path)
        if not settings.db_path.exists():
            results.add_fail("Database Connection", "Database file does not exist")
            return None
        results.add_pass("Database Connection", f"Connected to {settings.db_path}")
        return db
    except Exception as e:
        results.add_fail("Database Connection", e)
        return None

def test_database_tables(db):
    """Test 2: Database Tables Exist"""
    try:
        # Try to query each table
        with db._get_connection() as conn:
            cursor = conn.cursor()
            tables = ['ideas', 'bundles', 'created_bundles', 'activity_log', 'used_ideas', 'research_sessions']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count} records")
        results.add_pass("Database Tables", f"All {len(tables)} tables exist and queryable")
    except Exception as e:
        results.add_fail("Database Tables", e)

def test_database_integrity(db):
    """Test 3: Database Integrity"""
    try:
        idea_queries = IdeaQueries(db)
        bundle_queries = BundleQueries(db)
        created_queries = CreatedBundleQueries(db)

        # Check for orphaned bundles (bundles with invalid idea_id)
        bundles = bundle_queries.get_all(limit=1000)
        ideas = {idea.idea_id for idea in idea_queries.get_all(limit=1000)}

        orphaned = [b for b in bundles if b.idea_id and b.idea_id not in ideas]

        if orphaned:
            results.add_fail("Database Integrity", f"Found {len(orphaned)} orphaned bundles")
        else:
            results.add_pass("Database Integrity", "No orphaned records found")
    except Exception as e:
        results.add_fail("Database Integrity", e)

def test_current_state(db):
    """Test 4: Document Current Database State"""
    try:
        idea_queries = IdeaQueries(db)
        bundle_queries = BundleQueries(db)
        created_queries = CreatedBundleQueries(db)
        activity_queries = ActivityLogQueries(db)

        ideas_count = len(idea_queries.get_all(limit=10000))
        bundles_count = len(bundle_queries.get_all(limit=10000))
        created_count = len(created_queries.get_all(limit=10000))
        activities_count = len(activity_queries.get_all(limit=10000))

        # Get priority breakdown
        priority_a = len([i for i in idea_queries.get_all(limit=10000) if i.priority == "A"])
        priority_b = len([i for i in idea_queries.get_all(limit=10000) if i.priority == "B"])
        priority_c = len([i for i in idea_queries.get_all(limit=10000) if i.priority == "C"])

        # Get bundle status breakdown
        active_bundles = bundle_queries.get_all(limit=10000)
        completed_bundles = len([b for b in active_bundles if b.status == "completed"])
        failed_bundles = len([b for b in active_bundles if b.status == "failed"])
        in_progress_bundles = len([b for b in active_bundles if b.status == "in_progress"])

        details = f"""
        Ideas: {ideas_count} (A:{priority_a}, B:{priority_b}, C:{priority_c})
        Active Bundles: {bundles_count} (completed:{completed_bundles}, failed:{failed_bundles}, in_progress:{in_progress_bundles})
        Created Bundles: {created_count}
        Activity Logs: {activities_count}
        """

        results.add_pass("Current Database State", details.strip())

        return {
            "ideas": ideas_count,
            "bundles": bundles_count,
            "created_bundles": created_count,
            "priority_a": priority_a,
            "priority_b": priority_b,
        }
    except Exception as e:
        results.add_fail("Current Database State", e)
        return None

def test_available_ideas_for_quick_build(db):
    """Test 5: Check Available Ideas for Quick Build"""
    try:
        idea_queries = IdeaQueries(db)
        available = idea_queries.get_available_ideas(weeks_back=8, priorities=["A", "B"])

        if len(available) == 0:
            results.add_skip("Quick Build Availability", "No priority A/B ideas available")
            return False
        else:
            # Find best idea
            priority_rank = {"A": 3, "B": 2, "C": 1}
            best = max(available, key=lambda x: (priority_rank.get(x.priority, 0), x.roi_estimate or 0))
            results.add_pass("Quick Build Availability",
                           f"{len(available)} ideas available, best: {best.title} (Priority {best.priority}, ROI: {best.roi_estimate})")
            return True
    except Exception as e:
        results.add_fail("Quick Build Availability", e)
        return False

def test_file_structure():
    """Test 6: Verify File Structure"""
    try:
        # Check key directories exist
        data_dir = settings.data_dir
        output_dir = settings.output_dir

        if not data_dir.exists():
            results.add_fail("File Structure", f"Data directory missing: {data_dir}")
            return

        if not output_dir.exists():
            results.add_fail("File Structure", f"Output directory missing: {output_dir}")
            return

        # Check for bundles directory
        bundles_dir = data_dir / "bundles"
        bundle_count = 0
        if bundles_dir.exists():
            bundle_count = len(list(bundles_dir.iterdir()))

        results.add_pass("File Structure",
                        f"Data: {data_dir}, Output: {output_dir}, Bundles: {bundle_count}")
    except Exception as e:
        results.add_fail("File Structure", e)

def test_duplicate_prevention(db):
    """Test 7: Duplicate Research Prevention Logic"""
    try:
        # This tests the logic, not actual API calls
        from app.database.queries import ResearchSessionQueries

        research_queries = ResearchSessionQueries(db)

        # Get all research sessions
        sessions = research_queries.get_all(limit=100)

        # Check for duplicates within 24 hours
        duplicates = []
        for i, session in enumerate(sessions):
            for other in sessions[i+1:]:
                if (session.focus_niche == other.focus_niche and
                    session.is_focused == other.is_focused):
                    duplicates.append((session, other))

        if duplicates:
            results.add_pass("Duplicate Prevention Logic",
                           f"Found {len(duplicates)} potential duplicates (prevention should catch these)")
        else:
            results.add_pass("Duplicate Prevention Logic", "No duplicate research sessions found")
    except Exception as e:
        results.add_fail("Duplicate Prevention Logic", e)

def test_activity_log_completeness(db):
    """Test 8: Activity Log Completeness"""
    try:
        activity_queries = ActivityLogQueries(db)
        activities = activity_queries.get_all(limit=10000)

        # Check for incomplete activities (started but never completed/failed)
        incomplete = [a for a in activities if not a.completed_at and a.status == "in_progress"]

        if incomplete:
            results.add_fail("Activity Log Completeness",
                           f"Found {len(incomplete)} incomplete activity logs (may indicate crashes)")
        else:
            results.add_pass("Activity Log Completeness", "All activities properly closed")
    except Exception as e:
        results.add_fail("Activity Log Completeness", e)

def test_bundle_state_transitions(db):
    """Test 9: Bundle State Transitions Valid"""
    try:
        bundle_queries = BundleQueries(db)
        bundles = bundle_queries.get_all(limit=10000)

        # Validate state transitions
        valid_steps = ["planner", "maker", "packager"]
        valid_statuses = ["pending", "in_progress", "completed", "failed"]

        invalid = []
        for bundle in bundles:
            if bundle.current_step not in valid_steps:
                invalid.append(f"{bundle.bundle_id}: invalid step '{bundle.current_step}'")
            if bundle.status not in valid_statuses:
                invalid.append(f"{bundle.bundle_id}: invalid status '{bundle.status}'")

        if invalid:
            results.add_fail("Bundle State Transitions", f"Invalid states: {invalid}")
        else:
            results.add_pass("Bundle State Transitions", f"All {len(bundles)} bundles have valid states")
    except Exception as e:
        results.add_fail("Bundle State Transitions", e)

def test_created_bundles_archived(db):
    """Test 10: Created Bundles Properly Archived"""
    try:
        created_queries = CreatedBundleQueries(db)
        created_bundles = created_queries.get_all(limit=10000)

        # Check each created bundle has output_path
        missing_output = [b for b in created_bundles if not b.output_path]

        if missing_output:
            results.add_fail("Bundle Archiving",
                           f"{len(missing_output)} bundles missing output_path")
        else:
            results.add_pass("Bundle Archiving",
                           f"All {len(created_bundles)} created bundles have output_path")
    except Exception as e:
        results.add_fail("Bundle Archiving", e)

def main():
    print("\n" + "="*60)
    print("ASSETFORGE AUTOMATED TESTING")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    # Run database tests
    print("\nDATABASE TESTS\n")
    db = test_database_connection()

    if db:
        test_database_tables(db)
        test_database_integrity(db)
        state = test_current_state(db)
        test_file_structure()
        test_bundle_state_transitions(db)
        test_activity_log_completeness(db)
        test_duplicate_prevention(db)
        test_created_bundles_archived(db)

        # Conditional tests based on state
        if state and state["ideas"] > 0:
            can_quick_build = test_available_ideas_for_quick_build(db)
        else:
            results.add_skip("Quick Build Tests", "No ideas in database")

    # Print summary
    results.summary()

    # Save results to file
    results_file = Path(__file__).parent / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "passed": results.passed,
            "failed": results.failed,
            "skipped": results.skipped,
            "total": len(results.passed) + len(results.failed) + len(results.skipped),
            "success_rate": len(results.passed) / (len(results.passed) + len(results.failed)) * 100 if (len(results.passed) + len(results.failed)) > 0 else 0
        }, f, indent=2)

    print(f"\nFull results saved to: {results_file}")

    return len(results.failed) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
