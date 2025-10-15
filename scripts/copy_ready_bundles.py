"""
Script to create copies of "ready to make" bundles for testing

Usage:
    python scripts/copy_ready_bundles.py [--count N]
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import json
import secrets


def generate_bundle_id(prefix: str = "bundle-test") -> str:
    """Generate a unique bundle ID"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_suffix = secrets.token_hex(4)
    return f"{prefix}-{timestamp}-{random_suffix}"


def copy_bundle(conn: sqlite3.Connection, source_bundle: dict, new_bundle_id: str) -> bool:
    """Copy a bundle with a new ID"""
    try:
        cursor = conn.cursor()

        # Create new bundle with same data but new ID and timestamps
        cursor.execute("""
            INSERT INTO bundles (
                bundle_id, idea_id, created_at, updated_at,
                current_step, status, error_message, planner_output
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_bundle_id,
            source_bundle['idea_id'],
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            source_bundle['current_step'],
            source_bundle['status'],
            source_bundle['error_message'],
            source_bundle['planner_output']
        ))

        conn.commit()
        print(f"[OK] Created bundle: {new_bundle_id}")
        return True

    except sqlite3.IntegrityError as e:
        print(f"[ERROR] Bundle already exists or integrity error: {e}")
        return False
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return False


def main():
    # Parse arguments
    count = 6
    if len(sys.argv) > 1 and sys.argv[1] == "--count":
        try:
            count = int(sys.argv[2])
        except (IndexError, ValueError):
            print("Usage: python copy_ready_bundles.py [--count N]")
            sys.exit(1)

    # Find database
    # Try common locations
    possible_paths = [
        Path.home() / "AppData" / "Local" / "AssetForge" / "history.db",
        Path(__file__).parent.parent / "backend" / "history.db",
        Path("history.db"),
    ]

    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break

    if not db_path:
        print("[ERROR] Could not find database file. Tried:")
        for p in possible_paths:
            print(f"  - {p}")
        print("\nPlease specify database path manually or ensure AssetForge has been initialized.")
        sys.exit(1)

    print(f"Using database: {db_path}\n")

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find bundles ready for maker
    cursor.execute("""
        SELECT * FROM bundles
        WHERE current_step = 'planner' AND status = 'completed'
        ORDER BY updated_at DESC
        LIMIT 1
    """)

    source_bundle = cursor.fetchone()

    if not source_bundle:
        print("[ERROR] No bundles found with current_step='planner' and status='completed'")
        print("  Create a bundle plan first, then run this script.")
        conn.close()
        sys.exit(1)

    # Convert to dict
    source_dict = dict(source_bundle)

    print(f"Found source bundle: {source_dict['bundle_id']}")

    # Parse planner output to show what we're copying
    try:
        planner_data = json.loads(source_dict['planner_output'])
        print(f"  Title: {planner_data.get('title', 'Unknown')}")
        print(f"  Niche: {planner_data.get('niche', 'Unknown')}")
        print(f"  Assets: {len(planner_data.get('assets', []))}")
    except:
        pass

    print(f"\nCreating {count} copies...\n")

    # Create copies
    created_count = 0
    for i in range(count):
        new_id = generate_bundle_id(f"bundle-copy-{i+1}")
        if copy_bundle(conn, source_dict, new_id):
            created_count += 1

    conn.close()

    print(f"\n[OK] Successfully created {created_count}/{count} bundle copies")
    print("\nThese bundles are now available in the Library > Ready to Make tab")


if __name__ == "__main__":
    main()
