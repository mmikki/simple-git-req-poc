#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Default configuration
IMAGE_NAME=${IMAGE_NAME:-sgreq-tools:latest}
REQUIREMENTS_DIR=${REQUIREMENTS_DIR:-requirements}
VERIFICATION_DIR=${VERIFICATION_DIR:-verification}
OUTPUTS_DIR=${OUTPUTS_DIR:-outputs}

# Parse arguments
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUTS_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: bash scripts/run-reqs-toolkit.sh [OPTIONS]"
            echo ""
            echo "Run the requirements toolkit on the current directory."
            echo ""
            echo "Options:"
            echo "  -v, --verbose      Show verbose output"
            echo "  -i, --image NAME   Docker image to use (default: sgreq-tools:latest)"
            echo "  -o, --output DIR   Output directory (default: outputs)"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  IMAGE_NAME         Override default image name"
            echo "  REQUIREMENTS_DIR   Requirements directory (default: requirements)"
            echo "  VERIFICATION_DIR   Verification directory (default: verification)"
            echo "  OUTPUTS_DIR        Output directory (default: outputs)"
            echo ""
            echo "Examples:"
            echo "  bash scripts/run-reqs-toolkit.sh"
            echo "  bash scripts/run-reqs-toolkit.sh -v"
            echo "  bash scripts/run-reqs-toolkit.sh -i myreq:v1.0"
            echo "  IMAGE_NAME=myreq:dev bash scripts/run-reqs-toolkit.sh"
            echo ""
            echo "Running on a different project:"
            echo "  cd /path/to/other/project"
            echo "  bash /path/to/this/repo/scripts/run-reqs-toolkit.sh"
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
echo "Requirements Toolkit"
echo "=========================================="
echo ""

# Check if image exists
if ! docker images | grep -q "$(echo $IMAGE_NAME | cut -d: -f1)"; then
    echo -e "${RED}❌ Docker image not found: $IMAGE_NAME${NC}"
    echo ""
    echo "Build it first:"
    echo "  bash scripts/build-docker-image.sh"
    echo ""
    echo "Or specify a different image:"
    echo "  IMAGE_NAME=other:tag bash scripts/run-reqs-toolkit.sh"
    exit 1
fi

# Check if current directory has requirements structure
if [ ! -d "$REQUIREMENTS_DIR" ]; then
    echo -e "${YELLOW}⚠️  Warning: No '$REQUIREMENTS_DIR' directory found${NC}"
    echo "   Current directory: $(pwd)"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Create outputs directory if it doesn't exist
mkdir -p "$OUTPUTS_DIR"

echo -e "${BLUE}Configuration:${NC}"
echo "  Image:         $IMAGE_NAME"
echo "  Project dir:   $(pwd)"
echo "  Requirements:  $REQUIREMENTS_DIR"
echo "  Verification:  $VERIFICATION_DIR"
echo "  Outputs:       $OUTPUTS_DIR"
echo ""

# Get current user and group for proper file ownership
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

echo -e "${YELLOW}Running toolkit...${NC}"
echo ""

# Run the toolkit
DOCKER_RUN_CMD="docker run --rm \
  --user $CURRENT_UID:$CURRENT_GID \
  -v $(pwd):/repo \
  -w /repo \
  $IMAGE_NAME"

if [ "$VERBOSE" = true ]; then
    echo -e "${BLUE}Docker command:${NC}"
    echo "$DOCKER_RUN_CMD"
    echo ""
fi

if eval "$DOCKER_RUN_CMD"; then
    echo ""
    echo -e "${GREEN}✅ Toolkit completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Generated files:${NC}"
    ls -lh "$OUTPUTS_DIR"/ 2>/dev/null | tail -n +2 || echo "   (no files generated)"
    echo ""
    echo "View reports:"
    echo "  open $OUTPUTS_DIR/traceability_expandable.html"
    echo "  open $OUTPUTS_DIR/requirements.png"
else
    echo ""
    echo -e "${RED}❌ Toolkit failed${NC}"
    echo ""
    echo "Check the errors above for details."
    exit 1
fi