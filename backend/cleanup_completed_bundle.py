"""
Script to clean up a bundle that completed packaging but wasn't deleted from bundles table
"""

import sys
import io
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.database.db import DatabaseManager
from app.database.queries import BundleQueries
from app.settings import settings


def cleanup_bundle(bundle_id: str):
    """
    Delete a completed bundle from the bundles table
    (Should only exist in created_bundles after packaging)

    Args:
        bundle_id: Exact bundle ID to delete
    """
    db_manager = DatabaseManager(settings.db_path)
    bundle_queries = BundleQueries(db_manager)

    # Check if bundle exists
    bundle = bundle_queries.get_by_id(bundle_id)

    if not bundle:
        print(f"[NOT FOUND] Bundle '{bundle_id}' not in bundles table")
        print(f"This is actually correct - it should only be in created_bundles after packaging")
        db_manager.close()
        return True

    print(f"[FOUND] Bundle in bundles table:")
    print(f"  Bundle ID: {bundle.bundle_id}")
    print(f"  Current Step: {bundle.current_step}")
    print(f"  Status: {bundle.status}")
    print(f"  Updated: {bundle.updated_at}")

    if bundle.current_step == "packager" and bundle.status == "completed":
        print(f"\n[OK] This bundle completed packaging and should be removed from bundles table")

        success = bundle_queries.delete(bundle_id)

        if success:
            print(f"[SUCCESS] Deleted bundle from bundles table")
            print(f"           Bundle should now only exist in created_bundles (History)")
        else:
            print(f"[FAILED] Could not delete bundle")
            db_manager.close()
            return False
    else:
        print(f"\n[WARNING] Bundle is NOT in completed packager state")
        print(f"          Current: {bundle.current_step} ({bundle.status})")
        print(f"          Are you sure you want to delete it? (y/n)")

        response = input().strip().lower()
        if response == 'y':
            success = bundle_queries.delete(bundle_id)
            if success:
                print(f"[SUCCESS] Deleted bundle from bundles table")
            else:
                print(f"[FAILED] Could not delete bundle")
                db_manager.close()
                return False
        else:
            print(f"[CANCELLED] Bundle not deleted")
            db_manager.close()
            return False

    db_manager.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup_completed_bundle.py <bundle_id>")
        print("\nExample:")
        print("  python cleanup_completed_bundle.py bundle-test-02")
        sys.exit(1)

    bundle_id = sys.argv[1]
    cleanup_bundle(bundle_id)
