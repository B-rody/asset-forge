"""
Script to move a completed bundle back to "ready to package" state
This moves a bundle from created_bundles back to bundles table with maker step completed
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
from app.database.queries import BundleQueries, CreatedBundleQueries
from app.database.models import Bundle
from app.settings import settings
from datetime import datetime


def move_bundle_to_packager(bundle_id_pattern: str):
    """
    Move a bundle from created_bundles back to bundles table with status ready for packager

    Args:
        bundle_id_pattern: Part of the bundle ID to search for (case-insensitive)
    """
    # Initialize database
    db_manager = DatabaseManager(settings.db_path)
    created_bundle_queries = CreatedBundleQueries(db_manager)
    bundle_queries = BundleQueries(db_manager)

    # Find the bundle in created_bundles
    all_created = created_bundle_queries.get_all(limit=1000)

    matching_bundles = [
        b for b in all_created
        if bundle_id_pattern.lower() in b.bundle_id.lower()
    ]

    if not matching_bundles:
        print(f"[X] No bundles found matching: {bundle_id_pattern}")
        print(f"\nAvailable bundles in created_bundles:")
        for b in all_created[:10]:
            print(f"  - {b.bundle_id} ({b.title})")
        return False

    if len(matching_bundles) > 1:
        print(f"[!] Multiple bundles found matching '{bundle_id_pattern}':")
        for b in matching_bundles:
            print(f"  - {b.bundle_id} ({b.title})")
        print("\nPlease be more specific.")
        return False

    created_bundle = matching_bundles[0]
    print(f"[OK] Found bundle: {created_bundle.bundle_id}")
    print(f"  Title: {created_bundle.title}")
    print(f"  Niche: {created_bundle.niche}")

    # Create a new Bundle entry with maker step completed
    bundle = Bundle(
        bundle_id=created_bundle.bundle_id,
        idea_id=created_bundle.idea_id,
        created_at=created_bundle.created_at,
        updated_at=datetime.now().isoformat(),
        current_step="maker",
        status="completed",
        error_message=None,
        planner_output=created_bundle.planner_output
    )

    # Insert into bundles table
    success = bundle_queries.create(bundle)

    if success:
        print(f"\n[SUCCESS] Bundle moved to 'Ready to Package' state")
        print(f"   Current step: maker (completed)")
        print(f"   Bundle ID: {bundle.bundle_id}")

        # Optionally delete from created_bundles
        print(f"\n[NOTE] Bundle still exists in created_bundles (history)")
        print(f"   You can delete it from History panel if desired")
    else:
        print(f"\n[FAILED] Failed to move bundle (may already exist in bundles table)")

    db_manager.close()
    return success


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python move_bundle_to_packager.py <bundle_id_pattern>")
        print("\nExample:")
        print("  python move_bundle_to_packager.py adhd-focus")
        sys.exit(1)

    pattern = sys.argv[1]
    move_bundle_to_packager(pattern)
