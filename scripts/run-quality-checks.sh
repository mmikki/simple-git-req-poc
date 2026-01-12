#!/usr/bin/env bash
set -e

echo "=========================================="
echo "Running Python code quality checks"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TOOLS_DIR="tools"
FAILED=0

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dev dependencies
echo -e "${YELLOW}Installing development dependencies...${NC}"
pip install -q -r requirements-dev.txt
echo ""

# 1. Black - Code formatting check
echo "1. Running Black (code formatter)..."
if black --check --diff "$TOOLS_DIR"; then
    echo -e "${GREEN}✓ Black: Code formatting OK${NC}"
else
    echo -e "${RED}✗ Black: Code formatting issues found${NC}"
    echo "  Run: black tools/ to fix"
    FAILED=1
fi
echo ""

# 2. isort - Import sorting check
echo "2. Running isort (import sorting)..."
if isort --check-only --diff "$TOOLS_DIR"; then
    echo -e "${GREEN}✓ isort: Import order OK${NC}"
else
    echo -e "${RED}✗ isort: Import order issues found${NC}"
    echo "  Run: isort tools/ to fix"
    FAILED=1
fi
echo ""

# 3. flake8 - Style guide enforcement
echo "3. Running flake8 (style guide)..."
if flake8 "$TOOLS_DIR"; then
    echo -e "${GREEN}✓ flake8: Style guide compliance OK${NC}"
else
    echo -e "${RED}✗ flake8: Style guide violations found${NC}"
    FAILED=1
fi
echo ""

# 4. pylint - Code quality
echo "4. Running pylint (code quality)..."
if pylint "$TOOLS_DIR"/*.py; then
    echo -e "${GREEN}✓ pylint: Code quality OK${NC}"
else
    echo -e "${YELLOW}⚠ pylint: Some issues found (review manually)${NC}"
    # Don't fail on pylint warnings
fi
echo ""

# 5. mypy - Type checking
echo "5. Running mypy (type checking)..."
if mypy "$TOOLS_DIR"; then
    echo -e "${GREEN}✓ mypy: Type checking OK${NC}"
else
    echo -e "${RED}✗ mypy: Type checking issues found${NC}"
    FAILED=1
fi
echo ""

echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All quality checks passed!${NC}"
    exit 0
else
    echo -e "${RED}Some quality checks failed.${NC}"
    echo "Run the following to auto-fix formatting issues:"
    echo "  black tools/"
    echo "  isort tools/"
    exit 1
fi
