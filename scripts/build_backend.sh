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
    --output-dir=bin \
    --output-filename=assetforge_backend \
    --assume-yes-for-downloads \
    --enable-plugin=anti-bloat \
    --nofollow-import-to=pytest,unittest,test \
    --include-package-data=openai,pydantic \
    app/main.py

echo ""
echo "Build successful!"
echo "Binary: backend/bin/assetforge_backend"

deactivate
cd ..
