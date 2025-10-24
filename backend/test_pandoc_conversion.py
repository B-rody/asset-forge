"""
Test script for Pandoc/wkhtmltopdf markdown-to-PDF conversion

This script tests the Pandoc conversion pipeline without running the full agent workflow.
It replicates the same PATH setup and conversion logic used in asset_packager.py.

Usage:
    python backend/test_pandoc_conversion.py
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path


def get_pandoc_path() -> str:
    """
    Get path to bundled pandoc executable

    Returns path to bundled pandoc in backend/bin/, or falls back to system pandoc
    """
    # Determine base path - we're running from backend/
    base_path = Path(__file__).parent.resolve()

    # Platform-specific executable name
    if sys.platform == 'win32':
        pandoc_exe = base_path / 'bin' / 'pandoc.exe'
    elif sys.platform == 'darwin':
        pandoc_exe = base_path / 'bin' / 'pandoc'
    else:
        pandoc_exe = base_path / 'bin' / 'pandoc'

    # Resolve the full path to handle any symlinks or short names
    pandoc_exe = pandoc_exe.resolve()

    # Use bundled pandoc if it exists, otherwise fallback to system pandoc
    if pandoc_exe.exists():
        print(f"✓ Using bundled pandoc: {pandoc_exe}")
        return str(pandoc_exe)
    else:
        print(f"⚠ Bundled pandoc not found at {pandoc_exe}, using system pandoc")
        return 'pandoc'


def get_wkhtmltopdf_path() -> str:
    """
    Get path to bundled wkhtmltopdf executable

    Returns path to bundled wkhtmltopdf in backend/bin/wkhtmltopdf/bin/
    """
    # Determine base path - we're running from backend/
    base_path = Path(__file__).parent.resolve()

    # Platform-specific executable name (nested in wkhtmltopdf/bin subdirectory)
    if sys.platform == 'win32':
        wkhtmltopdf_exe = base_path / 'bin' / 'wkhtmltopdf' / 'bin' / 'wkhtmltopdf.exe'
    elif sys.platform == 'darwin':
        wkhtmltopdf_exe = base_path / 'bin' / 'wkhtmltopdf' / 'bin' / 'wkhtmltopdf'
    else:
        wkhtmltopdf_exe = base_path / 'bin' / 'wkhtmltopdf' / 'bin' / 'wkhtmltopdf'

    # Resolve the full path to handle any symlinks or short names
    wkhtmltopdf_exe = wkhtmltopdf_exe.resolve()

    # Use bundled wkhtmltopdf if it exists, otherwise fallback to system wkhtmltopdf
    if wkhtmltopdf_exe.exists():
        print(f"✓ Using bundled wkhtmltopdf: {wkhtmltopdf_exe}")
        return str(wkhtmltopdf_exe)
    else:
        print(f"⚠ Bundled wkhtmltopdf not found at {wkhtmltopdf_exe}, using system wkhtmltopdf")
        return 'wkhtmltopdf'


def generate_test_markdown() -> tuple[Path, str]:
    """
    Generate a test markdown file with random filename

    Returns:
        tuple: (file_path, random_id)
    """
    # Generate random ID for filename
    random_id = secrets.token_hex(4)

    # Create test directory if it doesn't exist
    test_dir = Path(__file__).parent / 'test_output'
    test_dir.mkdir(exist_ok=True)

    # Generate markdown filename with CONVERTPDF_ prefix
    md_filename = f"CONVERTPDF_test_{random_id}.md"
    md_path = test_dir / md_filename

    # Sample markdown content
    markdown_content = f"""# Weekly Habit Tracker Test

**Test ID:** {random_id}

This is a test document for validating Pandoc/wkhtmltopdf conversion.

---

## Introduction

This weekly habit tracker helps you monitor your daily routines and build consistency over time. Use this template to track habits, set goals, and reflect on your progress.

---

## How to Use This Tracker

Follow these simple steps to get started:

1. **Print or use digitally** - Choose your preferred format
2. **Check off habits daily** - Mark completed tasks
3. **Review weekly** - Analyze your progress
4. **Adjust as needed** - Modify habits based on results

---

## Daily Habit Checklist

### Monday

- [ ] Morning meditation (10 minutes)
- [ ] Exercise (30 minutes)
- [ ] Drink 8 glasses of water
- [ ] Read for 20 minutes
- [ ] Evening reflection

**Daily Notes:**
> Example: "Felt energized after morning workout. Need to improve water intake."

### Tuesday

- [ ] Morning meditation (10 minutes)
- [ ] Exercise (30 minutes)
- [ ] Drink 8 glasses of water
- [ ] Read for 20 minutes
- [ ] Evening reflection

**Daily Notes:**
> Example: "Started the day with a brisk walk. Finished chapter 3 of my book."

---

## Weekly Progress Table

| Day       | Meditation | Exercise | Water | Reading | Reflection |
|-----------|------------|----------|-------|---------|------------|
| Monday    | ✓          | ✓        | ✓     | ✓       | ✓          |
| Tuesday   | ✓          | ✓        | -     | ✓       | ✓          |
| Wednesday | ✓          | -        | ✓     | ✓       | ✓          |
| Thursday  | ✓          | ✓        | ✓     | -       | ✓          |
| Friday    | ✓          | ✓        | ✓     | ✓       | ✓          |
| Saturday  | -          | ✓        | ✓     | ✓       | -          |
| Sunday    | ✓          | -        | ✓     | ✓       | ✓          |

**Weekly Score:** 31/35 (89% completion)

---

## Weekly Reflection

### What went well this week?

> Example: "Maintained morning meditation 6 out of 7 days. Exercise routine became more consistent."

### What challenges did you face?

> Example: "Struggled to stay hydrated on busy workdays. Need to set phone reminders."

### Goals for next week

> Example: "Focus on weekend consistency. Add stretching to morning routine."

---

## Tips for Success

**Building Consistency:**
- Start small and gradually increase difficulty
- Link new habits to existing routines
- Track progress visually (checkmarks, graphs)
- Celebrate small wins

**Staying Motivated:**
- Review your 'why' regularly
- Find an accountability partner
- Reward yourself for milestones
- Be flexible and adjust as needed

**Overcoming Obstacles:**
- Plan for common barriers
- Have backup options ready
- Don't let one missed day derail you
- Focus on progress, not perfection

---

## Monthly Overview

Track your monthly habit completion rates:

| Week    | Completion Rate | Key Insights                          |
|---------|-----------------|---------------------------------------|
| Week 1  | 85%             | Strong start, maintained morning routine |
| Week 2  | 92%             | Best week! All systems working well   |
| Week 3  | 78%             | Busy week, need better planning       |
| Week 4  | 89%             | Back on track, ending strong          |

**Monthly Average:** 86%

---

## Notes & Observations

Use this space for additional thoughts, patterns you notice, or adjustments you want to make.

**Key Observations:**
- Morning habits are easier to maintain than evening ones
- Exercise boosts energy for the entire day
- Weekend consistency needs more attention
- Reading before bed improves sleep quality

**Adjustments for Next Month:**
- Set earlier bedtime to support morning routine
- Prepare workout clothes the night before
- Schedule weekend activities that include movement
- Create a dedicated reading nook

---

**End of Test Document - Test ID: {random_id}**
"""

    # Write markdown file
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"✓ Generated test markdown: {md_path}")
    return md_path, random_id


def convert_markdown_to_pdf(md_path: Path, pandoc_path: str, wkhtmltopdf_path: str) -> bool:
    """
    Convert markdown file to PDF using Pandoc and wkhtmltopdf

    Args:
        md_path: Path to markdown file
        pandoc_path: Path to pandoc executable
        wkhtmltopdf_path: Path to wkhtmltopdf executable

    Returns:
        bool: True if conversion succeeded, False otherwise
    """
    # Generate PDF path (remove CONVERTPDF_ prefix)
    pdf_name = md_path.name.replace("CONVERTPDF_", "").replace(".md", ".pdf")
    pdf_path = md_path.parent / pdf_name

    print(f"\n📄 Converting: {md_path.name} -> {pdf_name}")

    # Add wkhtmltopdf directory to PATH for DLL dependencies
    env = os.environ.copy()
    wkhtmltopdf_dir = str(Path(wkhtmltopdf_path).parent)

    if sys.platform == 'win32':
        env['PATH'] = f"{wkhtmltopdf_dir};{env.get('PATH', '')}"
    else:
        env['PATH'] = f"{wkhtmltopdf_dir}:{env.get('PATH', '')}"

    print(f"📂 Added to PATH: {wkhtmltopdf_dir}")

    # Build pandoc command with formatting options
    command = [
        pandoc_path,
        str(md_path),
        "-o",
        str(pdf_path),
        f"--pdf-engine={wkhtmltopdf_path}",
        "--css", "data:text/css,body{font-family:Arial,sans-serif;max-width:100%;margin:0.5in;background:white;color:#333;}h1{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:0.3em;margin-top:0.5em;}h2{color:#34495e;border-bottom:1px solid #bdc3c7;padding-bottom:0.2em;margin-top:0.4em;}table{border-collapse:collapse;width:100%;margin:1em 0;}th,td{border:1px solid #ddd;padding:8px;text-align:left;}th{background-color:#f2f2f2;}",
        "--metadata", "pagetitle=Test Document",
        "--pdf-engine-opt=--margin-top", "--pdf-engine-opt=0.5in",
        "--pdf-engine-opt=--margin-bottom", "--pdf-engine-opt=0.5in",
        "--pdf-engine-opt=--margin-left", "--pdf-engine-opt=0.5in",
        "--pdf-engine-opt=--margin-right", "--pdf-engine-opt=0.5in"
    ]

    print(f"\n🔧 Running command:")
    print(f"   {' '.join(command)}")

    try:
        # Run pandoc conversion
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )

        if result.returncode == 0:
            print(f"\n✅ SUCCESS! PDF generated at: {pdf_path}")
            print(f"   File size: {pdf_path.stat().st_size / 1024:.1f} KB")
            return True
        else:
            print(f"\n❌ FAILED! Pandoc returned error code {result.returncode}")

            if result.stderr:
                print(f"\n📋 Error details:")
                print(result.stderr)

            # Check for specific error patterns
            stderr_lower = result.stderr.lower() if result.stderr else ""
            if "wkhtmltopdf" in stderr_lower or "pdf-engine" in stderr_lower:
                print(f"\n💡 Hint: wkhtmltopdf may not be accessible. Check:")
                print(f"   1. wkhtmltopdf exists at: {wkhtmltopdf_path}")
                print(f"   2. Required DLLs are in: {wkhtmltopdf_dir}")
                print(f"   3. PATH includes: {wkhtmltopdf_dir}")

            return False

    except subprocess.TimeoutExpired:
        print(f"\n⏱️ TIMEOUT! Conversion took longer than 60 seconds")
        return False
    except Exception as e:
        print(f"\n💥 EXCEPTION! {type(e).__name__}: {e}")
        return False


def main():
    """Main test function"""
    print("=" * 70)
    print("🧪 Pandoc/wkhtmltopdf Conversion Test")
    print("=" * 70)
    print()

    # Get executable paths
    print("📍 Locating executables...")
    pandoc_path = get_pandoc_path()
    wkhtmltopdf_path = get_wkhtmltopdf_path()
    print()

    # Generate test markdown
    print("📝 Generating test markdown file...")
    md_path, random_id = generate_test_markdown()
    print()

    # Run conversion
    print("🔄 Starting conversion...")
    success = convert_markdown_to_pdf(md_path, pandoc_path, wkhtmltopdf_path)
    print()

    # Summary
    print("=" * 70)
    if success:
        print("✅ TEST PASSED")
        print(f"   Test ID: {random_id}")
        print(f"   Output directory: {md_path.parent}")
    else:
        print("❌ TEST FAILED")
        print(f"   Test ID: {random_id}")
        print(f"   Check the error messages above for details")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
