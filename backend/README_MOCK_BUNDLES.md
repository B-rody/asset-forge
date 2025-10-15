# Mock Bundle Generator

This script creates realistic mock bundles for testing the Packager agent without having to run the full pipeline.

## Usage

```bash
cd backend
python generate_mock_bundles.py
```

## What It Creates

The script generates **3 complete mock bundles**, each with:

1. **Database entries**:
   - Idea record in `ideas` table
   - Bundle record in `bundles` table with `current_step="maker"` and `status="completed"`
   - Complete planner output JSON

2. **File structure**:
   ```
   {data_dir}/bundles/{bundle_id}/
   └── maker_output/
       ├── asset-001-{name}/
       │   ├── CONVERTPDF_asset-001_{name}.md
       │   └── asset_metadata.json
       ├── asset-002-{name}/
       │   ├── CONVERTPDF_asset-002_{name}.md
       │   └── asset_metadata.json
       └── ...
   ```

3. **Realistic content**:
   - Markdown files with actual planner/tracker content
   - Asset metadata with proper format specifications
   - Ready for PDF conversion via Pandoc

## Mock Bundles Included

1. **Weekly Habit Tracker Bundle** (2 assets)
   - Weekly Habit Tracker (PDF)
   - Monthly Goals Planner (PDF)

2. **Budget Planner & Finance Tracker Bundle** (3 assets)
   - Monthly Budget Worksheet (PDF)
   - Expense Tracker Log (PDF)
   - Savings Goals Tracker (PDF)

3. **Content Creator Planner Bundle** (2 assets)
   - 30-Day Content Calendar (PDF)
   - Content Ideas Brainstorm Sheet (PDF)

## Testing the Packager

After running the script:

1. Start the AssetForge UI
2. Navigate to **Library > Ready to Generate** tab
3. You should see the 3 mock bundles listed
4. Click **"Generate Assets"** on any bundle to test the Packager

## What Gets Tested

The Packager will:
1. ✅ Collect asset metadata from all `asset_metadata.json` files
2. ✅ Generate store listings (title, description)
3. ✅ Convert `CONVERTPDF_*.md` files to PDFs using Pandoc
4. ✅ Create `bundle_metadata.md`
5. ✅ Copy final bundle to user's configured output directory
6. ✅ Archive bundle in `created_bundles` table

## Cleanup

The script creates new bundles each time it runs. If you want to clean up:

```bash
# Delete bundle directories
rm -rf C:\Users\{YOUR_USERNAME}\AppData\Local\AssetForge\bundles\mock-bundle-*

# Or delete the entire database to reset everything
rm C:\Users\{YOUR_USERNAME}\AppData\Local\AssetForge\history.db
```

## Requirements

- Python 3.12+
- AssetForge backend dependencies installed
- Database initialized (script will create it if needed)

## Notes

- Bundle IDs are generated with timestamp + random hex to avoid collisions
- All content is realistic and ready for actual marketplace listing
- Markdown content uses proper formatting for clean PDF conversion
- Asset metadata includes all required fields for packager validation
