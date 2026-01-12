#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Repository Cleanup Tool"
echo "=========================================="
echo ""

# Parse arguments
INTERACTIVE=true
FORCE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -y|--yes)
            INTERACTIVE=false
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: bash scripts/clean.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -f, --force        Skip confirmations"
            echo "  -y, --yes          Non-interactive (same as --force)"
            echo "  -d, --dry-run      Show what would be deleted (don't delete)"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  bash scripts/clean.sh              # Interactive cleanup"
            echo "  bash scripts/clean.sh --dry-run    # Preview what will be deleted"
            echo "  bash scripts/clean.sh -f           # Force cleanup without prompts"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Show what will be cleaned
echo -e "${BLUE}Items that will be cleaned:${NC}"
echo ""
echo "  📁 Python cache and compiled files:"
echo "     - __pycache__/ directories (all levels)"
echo "     - *.pyc, *.pyo files"
echo "     - *.egg-info/ directories"
echo "     - .Python files"
echo ""
echo "  🧪 Testing artifacts:"
echo "     - .pytest_cache/"
echo "     - .coverage"
echo "     - htmlcov/"
echo "     - *.cover"
echo "     - .mypy_cache/"
echo "     - coverage.xml"
echo ""
echo "  📊 Generated outputs (OPTIONAL):"
echo "     - outputs/*.json"
echo "     - outputs/*.csv"
echo "     - outputs/*.html"
echo "     - outputs/*.dot"
echo "     - outputs/*.png"
echo ""
echo "  🐳 Docker artifacts (OPTIONAL):"
echo "     - Dangling Docker images"
echo "     - Docker build cache"
echo ""

# Show dry-run status
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE - No files will be deleted${NC}"
    echo ""
fi

# Ask user what to clean
CLEAN_OUTPUTS=false
CLEAN_DOCKER=false

if [ "$INTERACTIVE" = true ] && [ "$DRY_RUN" = false ]; then
    echo -e "${YELLOW}What would you like to clean?${NC}"
    echo ""
    
    read -p "Clean Python cache and test artifacts? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        CLEAN_ALL=true
    fi
    
    read -p "Also clean generated outputs (outputs/*)? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        CLEAN_OUTPUTS=true
    fi
    
    read -p "Also clean Docker artifacts? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        CLEAN_DOCKER=true
    fi
    
    if [ "$FORCE" = false ]; then
        echo ""
        read -p "Proceed with cleanup? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Cleanup cancelled${NC}"
            exit 0
        fi
    fi
elif [ "$DRY_RUN" = false ]; then
    # Force mode - clean everything
    CLEAN_OUTPUTS=true
    CLEAN_DOCKER=true
fi

echo ""
echo "=========================================="
echo -e "${YELLOW}Starting cleanup...${NC}"
echo "=========================================="
echo ""

DELETED=0

# Function to delete with dry-run support
delete_with_find() {
    local pattern=$1
    local description=$2
    local type=${3:--name}  # default to -name, can be -type
    
    if [ "$DRY_RUN" = true ]; then
        local count=$(find . $type "$pattern" 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            echo -e "${BLUE}[DRY RUN]${NC} Would delete $count item(s) matching: $pattern"
            find . $type "$pattern" 2>/dev/null | head -5
            if [ "$count" -gt 5 ]; then
                echo "         ... and $((count - 5)) more"
            fi
        fi
    else
        local count=$(find . $type "$pattern" 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            find . $type "$pattern" -exec rm -rf {} + 2>/dev/null || true
            echo -e "${GREEN}✓${NC} Deleted $count item(s) matching: $pattern"
            ((DELETED++))
        fi
    fi
}

# 1. Clean Python cache
echo -e "${YELLOW}1. Cleaning Python cache and compiled files...${NC}"

# Delete __pycache__ directories recursively (any depth)
delete_with_find "__pycache__" "pycache directories" "-type d"

# Delete compiled Python files
delete_with_find "*.pyc" "compiled Python files"
delete_with_find "*.pyo" "optimized Python files"

# Delete egg-info directories
delete_with_find "*.egg-info" "egg-info directories" "-type d"

# Delete .Python files
delete_with_find ".Python" "Python marker files"

echo -e "${GREEN}✓ Python cache cleaned${NC}"
echo ""

# 2. Clean test artifacts
echo -e "${YELLOW}2. Cleaning test artifacts...${NC}"

# Delete pytest cache
if [ -d ".pytest_cache" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN]${NC} Would delete: .pytest_cache/"
    else
        rm -rf .pytest_cache
        echo -e "${GREEN}✓${NC} Deleted: .pytest_cache/"
        ((DELETED++))
    fi
fi

# Delete mypy cache
if [ -d ".mypy_cache" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN]${NC} Would delete: .mypy_cache/"
    else
        rm -rf .mypy_cache
        echo -e "${GREEN}✓${NC} Deleted: .mypy_cache/"
        ((DELETED++))
    fi
fi

# Delete coverage data
if [ -f ".coverage" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN]${NC} Would delete: .coverage"
    else
        rm -f .coverage
        echo -e "${GREEN}✓${NC} Deleted: .coverage"
        ((DELETED++))
    fi
fi

# Delete HTML coverage report
if [ -d "htmlcov" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN]${NC} Would delete: htmlcov/"
    else
        rm -rf htmlcov
        echo -e "${GREEN}✓${NC} Deleted: htmlcov/"
        ((DELETED++))
    fi
fi

# Delete coverage files
delete_with_find "*.cover" "coverage files"
delete_with_find "coverage.xml" "coverage XML reports"

echo -e "${GREEN}✓ Test artifacts cleaned${NC}"
echo ""

# 3. Clean outputs (optional)
if [ "$CLEAN_OUTPUTS" = true ]; then
    echo -e "${YELLOW}3. Cleaning generated outputs...${NC}"
    if [ -d "outputs" ]; then
        if [ "$DRY_RUN" = true ]; then
            local count=$(find outputs -maxdepth 1 -type f \( -name "*.json" -o -name "*.csv" -o -name "*.html" -o -name "*.dot" -o -name "*.png" \) 2>/dev/null | wc -l)
            if [ "$count" -gt 0 ]; then
                echo -e "${BLUE}[DRY RUN]${NC} Would delete $count file(s) from outputs/"
                find outputs -maxdepth 1 -type f \( -name "*.json" -o -name "*.csv" -o -name "*.html" -o -name "*.dot" -o -name "*.png" \) 2>/dev/null
            fi
        else
            rm -f outputs/*.json outputs/*.csv outputs/*.html outputs/*.dot outputs/*.png 2>/dev/null || true
            echo -e "${GREEN}✓ Generated outputs cleaned${NC}"
            ((DELETED++))
        fi
    fi
    echo ""
fi

# 4. Clean Docker artifacts (optional)
if [ "$CLEAN_DOCKER" = true ]; then
    echo -e "${YELLOW}4. Cleaning Docker artifacts...${NC}"
    
    # Remove dangling images
    if docker images --filter "dangling=true" -q 2>/dev/null | grep -q .; then
        if [ "$DRY_RUN" = true ]; then
            local count=$(docker images --filter "dangling=true" -q 2>/dev/null | wc -l)
            echo -e "${BLUE}[DRY RUN]${NC} Would remove $count dangling Docker image(s)"
            docker images --filter "dangling=true" 2>/dev/null | head -5
        else
            docker image prune -f --filter "dangling=true" > /dev/null 2>&1 || true
            echo -e "${GREEN}✓ Dangling Docker images removed${NC}"
            ((DELETED++))
        fi
    else
        echo -e "${GREEN}✓ No dangling Docker images${NC}"
    fi
    
    # Clean build cache (optional)
    if [ "$FORCE" = true ] && [ "$DRY_RUN" = false ]; then
        docker builder prune -af --filter "unused-for=1h" > /dev/null 2>&1 || true
        echo -e "${GREEN}✓ Docker build cache pruned${NC}"
        ((DELETED++))
    fi
    echo ""
fi

# 5. Summary
echo "=========================================="
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN COMPLETE${NC}"
    echo ""
    echo "Run without --dry-run to actually delete files:"
    echo "  bash scripts/clean.sh"
else
    if [ "$DELETED" -gt 0 ]; then
        echo -e "${GREEN}✅ Cleanup complete!${NC}"
        echo ""
        echo "Removed:"
        echo "  - Python cache and compiled files"
        echo "  - Test artifacts and coverage reports"
        if [ "$CLEAN_OUTPUTS" = true ]; then
            echo "  - Generated outputs"
        fi
        if [ "$CLEAN_DOCKER" = true ]; then
            echo "  - Docker artifacts"
        fi
    else
        echo -e "${GREEN}✅ Nothing to clean!${NC}"
    fi
fi
echo "=========================================="
echo ""
EOF

chmod +x scripts/clean.sh