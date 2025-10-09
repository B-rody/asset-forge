#!/bin/bash
# Run Python backend in development mode (Unix/Mac)

set -e

echo "Starting AssetForge backend (dev mode)..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run backend
python app/main.py

deactivate
cd ..
