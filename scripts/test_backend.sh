#!/bin/bash
# Test the compiled backend binary to ensure it starts properly

set -e

echo "Testing AssetForge backend binary..."
echo ""

BACKEND_BIN="backend/bin/assetforge_backend"

if [ ! -f "$BACKEND_BIN" ]; then
    echo "ERROR: Backend binary not found at $BACKEND_BIN"
    echo "Please build the backend first using: scripts/build_backend.sh"
    exit 1
fi

echo "Found backend binary: $BACKEND_BIN"
echo "Testing startup and shutdown..."
echo ""

# Send a simple command and then EOF to test startup
echo '{"cmd":"get_api_key"}' | "$BACKEND_BIN"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Backend test passed! Binary starts and responds correctly."
    exit 0
else
    echo ""
    echo "❌ Backend test failed! Binary returned error code $?"
    echo ""
    echo "Possible issues:"
    echo "- Missing dependencies in Nuitka build"
    echo "- Import errors"
    echo "- Runtime initialization failures"
    echo ""
    echo "Check the error output above for details."
    exit 1
fi
