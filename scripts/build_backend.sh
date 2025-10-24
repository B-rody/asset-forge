#!/bin/bash
# Build Python backend with Nuitka (Unix/Mac)

set -e

echo "Building AssetForge backend with Nuitka..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install nuitka ordered-set zstandard

# Build with Nuitka (standalone mode for debugging)
echo "Compiling with Nuitka in STANDALONE mode..."
echo "This creates a folder with all dependencies visible for debugging."
python -m nuitka \
    --standalone \
    --jobs=0 \
    --output-dir=bin \
    --assume-yes-for-downloads \
    --nofollow-import-to=pytest,unittest,test \
    --include-package=app \
    --include-package=openai \
    --include-package=pydantic \
    --include-package=pydantic_core \
    --include-package=rich \
    --include-package=orjson \
    --include-package=cryptography \
    --include-package=platformdirs \
    --include-package=jsonschema \
    --include-package=dateutil \
    --include-package=tenacity \
    --include-data-dir=app/pipeline/agents/prompts=app/pipeline/agents/prompts \
    --include-data-dir=app/pipeline/agents/asset_agents/prompts=app/pipeline/agents/asset_agents/prompts \
    --include-data-dir=app/pipeline/agents/schemas=app/pipeline/agents/schemas \
    --include-data-dir=app/pipeline/agents/asset_agents/schemas=app/pipeline/agents/asset_agents/schemas \
    --include-data-file=bin/pandoc=bin/pandoc \
    --include-data-file=bin/wkhtmltopdf/bin/wkhtmltopdf=bin/wkhtmltopdf/bin/wkhtmltopdf \
    --include-data-file=bin/wkhtmltopdf/bin/wkhtmltoimage=bin/wkhtmltopdf/bin/wkhtmltoimage \
    --include-data-file=bin/wkhtmltopdf/bin/vcruntime140.dll=bin/wkhtmltopdf/bin/vcruntime140.dll \
    --include-data-file=bin/wkhtmltopdf/bin/vcruntime140_1.dll=bin/wkhtmltopdf/bin/vcruntime140_1.dll \
    --include-data-file=bin/wkhtmltopdf/bin/msvcp140.dll=bin/wkhtmltopdf/bin/msvcp140.dll \
    app/main.py

echo ""
echo "========================================"
echo "STANDALONE MODE OUTPUT"
echo "========================================"
echo "Executable: backend/bin/main.dist/main"
echo "Libraries folder: backend/bin/main.dist/"
echo ""
echo "To inspect bundled libraries, check the main.dist folder."
echo "All dependencies should be visible there."
echo ""
echo "To test: cd backend/bin/main.dist && ./main"
echo "========================================"
echo ""

# Don't clean up in standalone mode - we need to inspect the output
echo "Cleaning temporary build artifacts only..."
rm -rf bin/main.build
echo "✅ Backend build completed successfully!"

deactivate
cd ..
