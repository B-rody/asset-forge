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

# Build with Nuitka
echo "Compiling with Nuitka..."
python -m nuitka \
    --standalone \
    --onefile \
    --jobs=0 \
    --output-dir=bin \
    --output-filename=assetforge_backend \
    --assume-yes-for-downloads \
    --enable-plugin=anti-bloat \
    --nofollow-import-to=pytest,unittest,test \
    --include-package-data=openai,pydantic \
    --include-module=cryptography \
    --include-module=orjson \
    --include-module=keyring \
    --include-module=sqlite3 \
    app/main.py

echo ""
echo "Build successful!"
echo "Binary: backend/bin/assetforge_backend"

# Clean up Nuitka build artifacts to reduce bundle size
echo "Cleaning build artifacts..."
rm -rf bin/main.build
rm -rf bin/main.dist
rm -rf bin/main.onefile-build
echo "✅ Backend build completed successfully!"

deactivate
cd ..
