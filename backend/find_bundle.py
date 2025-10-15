"""
Diagnostic script to find a bundle across all database tables
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
from app.settings import settings


def find_bundle(bundle_id_pattern: str):
    """
    Search for a bundle across all tables

    Args:
        bundle_id_pattern: Part of the bundle ID to search for (case-insensitive)
    """
    db_manager = DatabaseManager(settings.db_path)
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    print(f"\n{'='*70}")
    print(f"Searching for bundles matching: '{bundle_id_pattern}'")
    print(f"{'='*70}\n")

    # Search in bundles table (active work)
    print("[1] Checking 'bundles' table (active work)...")
    cursor.execute("""
        SELECT bundle_id, idea_id, current_step, status, error_message, updated_at
        FROM bundles
        WHERE bundle_id LIKE ?
    """, (f"%{bundle_id_pattern}%",))

    bundles_results = cursor.fetchall()
    if bundles_results:
        print(f"   Found {len(bundles_results)} entry/entries:\n")
        for row in bundles_results:
            print(f"   Bundle ID: {row['bundle_id']}")
            print(f"   Idea ID: {row['idea_id']}")
            print(f"   Current Step: {row['current_step']}")
            print(f"   Status: {row['status']}")
            print(f"   Error: {row['error_message'] or 'None'}")
            print(f"   Updated: {row['updated_at']}")
            print()
    else:
        print("   [NOT FOUND]\n")

    # Search in created_bundles table (completed/archived)
    print("[2] Checking 'created_bundles' table (completed/history)...")
    cursor.execute("""
        SELECT bundle_id, idea_id, title, niche, completed_at
        FROM created_bundles
        WHERE bundle_id LIKE ?
    """, (f"%{bundle_id_pattern}%",))

    created_results = cursor.fetchall()
    if created_results:
        print(f"   Found {len(created_results)} entry/entries:\n")
        for row in created_results:
            print(f"   Bundle ID: {row['bundle_id']}")
            print(f"   Idea ID: {row['idea_id']}")
            print(f"   Title: {row['title']}")
            print(f"   Niche: {row['niche']}")
            print(f"   Completed: {row['completed_at']}")
            print()
    else:
        print("   [NOT FOUND]\n")

    # Search in ideas table (source ideas)
    print("[3] Checking 'ideas' table (available ideas)...")
    cursor.execute("""
        SELECT idea_id, title, niche, priority
        FROM ideas
        WHERE idea_id LIKE ? OR title LIKE ?
    """, (f"%{bundle_id_pattern}%", f"%{bundle_id_pattern}%"))

    ideas_results = cursor.fetchall()
    if ideas_results:
        print(f"   Found {len(ideas_results)} entry/entries:\n")
        for row in ideas_results:
            print(f"   Idea ID: {row['idea_id']}")
            print(f"   Title: {row['title']}")
            print(f"   Niche: {row['niche']}")
            print(f"   Priority: {row['priority']}")
            print()
    else:
        print("   [NOT FOUND]\n")

    # Summary
    print(f"{'='*70}")
    print(f"SUMMARY:")
    print(f"  - bundles table: {len(bundles_results)} result(s)")
    print(f"  - created_bundles table: {len(created_results)} result(s)")
    print(f"  - ideas table: {len(ideas_results)} result(s)")
    print(f"{'='*70}\n")

    db_manager.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_bundle.py <bundle_id_pattern>")
        print("\nExample:")
        print("  python find_bundle.py bundle-test-02")
        print("  python find_bundle.py adhd")
        sys.exit(1)

    pattern = sys.argv[1]
    find_bundle(pattern)
