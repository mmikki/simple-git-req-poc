#!/usr/bin/env bash
set -e

echo "=========================================="
echo "Formatting Python code"
echo "=========================================="
echo ""

TOOLS_DIR="tools"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dev dependencies
echo "Installing development dependencies..."
pip install -q -r requirements-dev.txt
echo ""

# Format with black
echo "1. Running Black..."
black "$TOOLS_DIR"
echo ""

# Sort imports
echo "2. Running isort..."
isort "$TOOLS_DIR"
echo ""

echo "=========================================="
echo "Code formatting complete!"
echo "=========================================="
