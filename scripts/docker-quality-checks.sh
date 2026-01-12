#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Running Code Quality Checks (Docker)"
echo "=========================================="
echo ""

IMAGE_NAME="req-formatter"

# Build image if needed
if ! docker images | grep -q "$IMAGE_NAME"; then
    echo -e "${YELLOW}Building quality check image...${NC}"
    docker build -f Dockerfile.formatter -t $IMAGE_NAME .
    echo ""
fi

# Get current user and group for proper file ownership
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

# Function to run a command in Docker with proper permissions
run_check() {
    docker run --rm \
        --user "$CURRENT_UID:$CURRENT_GID" \
        -v "$(pwd):/workspace" \
        $IMAGE_NAME \
        "$1"
}

FAILED=0

# 1. Black
echo -e "${YELLOW}1. Running Black (code formatter)...${NC}"
if run_check "black tools/ --check --diff" 2>&1; then
    echo -e "${GREEN}✓ Black: Code formatting OK${NC}"
else
    echo -e "${RED}✗ Black: Code formatting issues found${NC}"
    echo "  Run: bash scripts/format.sh"
    FAILED=1
fi
echo ""

# 2. isort
echo -e "${YELLOW}2. Running isort (import sorting)...${NC}"
if run_check "isort tools/ --check-only --diff" 2>&1; then
    echo -e "${GREEN}✓ isort: Import order OK${NC}"
else
    echo -e "${RED}✗ isort: Import order issues found${NC}"
    echo "  Run: bash scripts/format.sh"
    FAILED=1
fi
echo ""

# 3. flake8
echo -e "${YELLOW}3. Running flake8 (style guide)...${NC}"
if run_check "flake8 tools/ --max-line-length=100 --extend-ignore=E203,W503" 2>&1; then
    echo -e "${GREEN}✓ flake8: Style guide compliance OK${NC}"
else
    echo -e "${RED}✗ flake8: Style guide violations found${NC}"
    FAILED=1
fi
echo ""

# 4. pylint
echo -e "${YELLOW}4. Running pylint (code quality)...${NC}"
if run_check "pylint tools/ --max-line-length=100" 2>&1; then
    echo -e "${GREEN}✓ pylint: Code quality OK${NC}"
else
    echo -e "${RED}✗ pylint: Code quality issues found${NC}"
    FAILED=1
fi
echo ""

# 5. mypy
echo -e "${YELLOW}5. Running mypy (type checking)...${NC}"
if run_check "mypy tools/ --config-file pyproject.toml" 2>&1; then
    echo -e "${GREEN}✓ mypy: Type checking OK${NC}"
else
    echo -e "${RED}✗ mypy: Type checking issues found${NC}"
    FAILED=1
fi
echo ""

echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All quality checks passed!${NC}"
else
    echo -e "${RED}Some quality checks failed.${NC}"
    echo "Run: bash scripts/format.sh to auto-fix formatting"
fi
echo "=========================================="

exit $FAILED
