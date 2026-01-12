#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
IMAGE_NAME=${IMAGE_NAME:-sgreq-tools:latest}
DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-1}
FORCE_REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE_REBUILD=true
            shift
            ;;
        -t|--tag)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: bash scripts/build-docker-image.sh [OPTIONS]"
            echo ""
            echo "Build the requirements toolkit Docker image."
            echo ""
            echo "Options:"
            echo "  -f, --force        Force rebuild (no cache)"
            echo "  -t, --tag NAME     Image name (default: sgreq-tools:latest)"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  IMAGE_NAME         Override default image name"
            echo "  DOCKER_BUILDKIT    Enable BuildKit (default: 1)"
            echo ""
            echo "Examples:"
            echo "  bash scripts/build-docker-image.sh"
            echo "  bash scripts/build-docker-image.sh -f"
            echo "  bash scripts/build-docker-image.sh -t myreq:v1.0"
            echo "  IMAGE_NAME=myreq:dev bash scripts/build-docker-image.sh"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Building Requirements Toolkit Docker Image"
echo "=========================================="
echo ""
echo -e "${BLUE}Image name:${NC} $IMAGE_NAME"
echo -e "${BLUE}BuildKit:${NC} $DOCKER_BUILDKIT"
if [ "$FORCE_REBUILD" = true ]; then
    echo -e "${BLUE}Mode:${NC} Force rebuild (no cache)"
fi
echo ""

# Build command
BUILD_CMD="docker build -t $IMAGE_NAME"

if [ "$FORCE_REBUILD" = true ]; then
    BUILD_CMD="$BUILD_CMD --no-cache"
fi

BUILD_CMD="$BUILD_CMD ."

echo -e "${YELLOW}Building image...${NC}"
if DOCKER_BUILDKIT=$DOCKER_BUILDKIT eval "$BUILD_CMD"; then
    echo ""
    echo -e "${GREEN}✅ Image built successfully!${NC}"
    echo ""
    echo "Image: $IMAGE_NAME"
    echo ""
    echo "Next steps:"
    echo "  bash scripts/run-reqs-toolkit.sh          # Run on current directory"
    echo "  cd /path/to/project && bash scripts/run-reqs-toolkit.sh  # Run elsewhere"
    echo ""
    echo "Or specify image explicitly:"
    echo "  IMAGE_NAME=$IMAGE_NAME bash scripts/run-reqs-toolkit.sh"
else
    echo ""
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi