#!/usr/bin/env bash
set -euo pipefail

# This is a convenience wrapper that builds (if needed) and runs the toolkit

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

IMAGE_NAME=${IMAGE_NAME:-sgreq-tools:latest}

echo "=========================================="
echo "Requirements Toolkit (Build + Run)"
echo "=========================================="
echo ""

# Check if image exists
if ! docker images | grep -q "$(echo $IMAGE_NAME | cut -d: -f1)"; then
    echo -e "${YELLOW}Image not found. Building first...${NC}"
    echo ""
    bash "$(dirname "$0")/build-docker-image.sh"
    echo ""
fi

# Run the toolkit
echo -e "${YELLOW}Running toolkit on current directory...${NC}"
echo ""
bash "$(dirname "$0")/run-reqs-toolkit.sh" "$@"
