"""
One-time script to clean OpenAI citation markers from existing database records
"""

import sqlite3
import json
import re
from pathlib import Path


def strip_citations(data):
    """
    Recursively strip OpenAI citation markers from data structures.

    Citation markers follow the pattern: \ue200cite\ue202<refs>\ue201
    """
    if isinstance(data, dict):
        return {key: strip_citations(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [strip_citations(item) for item in data]
    elif isinstance(data, str):
        # Strip citation markers and clean trailing whitespace
        cleaned = re.sub(r'\ue200cite\ue202[^\ue201]*\ue201', '', data)
        return cleaned.strip()
    else:
        return data


def clean_database():
    """Clean citation markers from all ideas in the database"""

    # Database path
    db_path = Path.home() / "AppData" / "Local" / "AssetForge" / "history.db"

    if not db_path.exists():
        print(f"[ERROR] Database not found at: {db_path}")
        return

    print(f"[INFO] Opening database: {db_path}")

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get all ideas
        cursor.execute("SELECT idea_id, idea_json FROM ideas")
        ideas = cursor.fetchall()

        print(f"\n[INFO] Found {len(ideas)} ideas to process")

        if len(ideas) == 0:
            print("[INFO] No ideas to clean")
            return

        cleaned_count = 0

        # Process each idea
        for idea in ideas:
            idea_id = idea['idea_id']
            idea_json = idea['idea_json']

            try:
                # Parse JSON
                idea_data = json.loads(idea_json)

                # Strip citations
                cleaned_data = strip_citations(idea_data)

                # Re-serialize
                cleaned_json = json.dumps(cleaned_data, ensure_ascii=False)

                # Update database only if changed
                if cleaned_json != idea_json:
                    cursor.execute(
                        "UPDATE ideas SET idea_json = ? WHERE idea_id = ?",
                        (cleaned_json, idea_id)
                    )
                    cleaned_count += 1
                    print(f"  [OK] Cleaned: {idea_id}")
                else:
                    print(f"  [SKIP] No citations found: {idea_id}")

            except json.JSONDecodeError as e:
                print(f"  [ERROR] Failed to parse JSON for {idea_id}: {e}")
            except Exception as e:
                print(f"  [ERROR] Error processing {idea_id}: {e}")

        # Commit changes
        conn.commit()

        print(f"\n[SUCCESS] Cleanup complete!")
        print(f"   Total ideas: {len(ideas)}")
        print(f"   Cleaned: {cleaned_count}")
        print(f"   Unchanged: {len(ideas) - cleaned_count}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        conn.rollback()

    finally:
        conn.close()
        print("\n[INFO] Database connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("Citation Cleanup Script")
    print("=" * 60)

    clean_database()

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
