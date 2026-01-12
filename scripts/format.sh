#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Formatting Code (Docker)"
echo "=========================================="
echo ""

IMAGE_NAME="req-formatter"

# Build formatter image if needed
if ! docker images | grep -q "$IMAGE_NAME"; then
    echo -e "${YELLOW}Building formatter image (one-time setup)...${NC}"
    docker build -f Dockerfile.formatter -t $IMAGE_NAME .
    echo ""
fi

# Get current user and group for proper file ownership
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

# Run formatters with proper user permissions
echo -e "${YELLOW}Running Black...${NC}"
docker run --rm \
    --user "$CURRENT_UID:$CURRENT_GID" \
    -v "$(pwd):/workspace" \
    $IMAGE_NAME \
    "black tools/ $*"
echo ""

echo -e "${YELLOW}Running isort...${NC}"
docker run --rm \
    --user "$CURRENT_UID:$CURRENT_GID" \
    -v "$(pwd):/workspace" \
    $IMAGE_NAME \
    "isort tools/ $*"
echo ""

echo -e "${GREEN}✓ Formatting complete!${NC}"
