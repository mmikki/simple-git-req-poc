#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Running Unit Tests (Docker)"
echo "=========================================="
echo ""

IMAGE_NAME="req-formatter"

# Build image if needed
if ! docker images | grep -q "$IMAGE_NAME"; then
    echo -e "${YELLOW}Building test image...${NC}"
    docker build -f Dockerfile.formatter -t $IMAGE_NAME .
    echo ""
fi

# Get current user and group for proper file ownership
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

# Run pytest with proper user permissions
echo -e "${YELLOW}Running pytest...${NC}"
echo ""

if docker run --rm \
    --user "$CURRENT_UID:$CURRENT_GID" \
    -v "$(pwd):/workspace" \
    $IMAGE_NAME \
    "pytest tests/ --cov=tools --cov-report=term-missing $*"; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
