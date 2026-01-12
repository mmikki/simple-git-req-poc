# Simple Git Requirements POC

A proof-of-concept system for managing requirements using Git and Markdown, with automatic traceability matrix generation.

**🎯 Key Features:**
- 📝 Markdown-based requirements with YAML front matter
- 🔗 Automatic traceability tracking across all levels
- 📊 Multiple export formats (HTML, CSV, Graphviz)
- ✅ Built-in validation and quality checks
- 🐳 Docker-based tooling (no local Python install needed!)
- 🏆 10/10 code quality score (pylint, mypy, black, isort, flake8)

## Quick Start

### Prerequisites
- Docker (that's it!)
- Git

### Generate Traceability Reports

```bash
# Run all tools (builds traceability, generates reports)
bash scripts/run-toolkit-with-docker.sh
```

This generates:
- **`outputs/traceability.html`** - Full traceability matrix
- **`outputs/traceability_expandable.html`** - Interactive expandable view
- **`outputs/traceability.csv`** - Spreadsheet format
- **`outputs/requirements.dot`** - Graphviz visualization
- **`outputs/trace.json`** - Structured data for custom analysis

## Project Structure

```
simple-git-req-poc/
├── requirements/               # Requirement definitions
│   ├── business/              # BR-XXX: Business requirements
│   ├── system/                # SR-XXX: System requirements
│   ├── software/              # TR-XXX: Technical requirements
│   └── templates/             # Requirement templates
├── verification/              
│   ├── requirements/          # TRQ-XXX: Test requirements
│   ├── test-cases/            # TC-XXX: Test cases
│   └── templates/             # Test templates
├── tools/                     # Python automation scripts
│   ├── common.py             # Shared utilities (DRY)
│   ├── build_traceability.py # Parse and build trace database
│   ├── validate_requirements.py # Validate structure and links
│   ├── export_html*.py       # HTML exporters
│   ├── export_graphviz.py    # Graph visualization
│   └── export_matrix_csv.py  # CSV export
├── scripts/                   # Automation scripts
│   ├── run-toolkit-with-docker.sh  # Run all tools
│   ├── format.sh             # Format code (Docker)
│   └── docker-quality-checks.sh    # Quality checks (Docker)
├── outputs/                   # Generated reports
├── docs/                      # Documentation
└── Dockerfile.formatter       # Docker image for dev tools
```

## Requirement Hierarchy

The project uses a 5-level requirement and verification hierarchy:

```
Business Requirements (BR)
    ↓ derives
System Requirements (SR)
    ↓ derives
Software Requirements (TR)
    ↓ verified_by
Test Requirements (TRQ)
    ↓ tested_by
Test Cases (TC)
```

### Levels Explained

1. **Business Requirements (BR)** - *What the business needs*
   - Location: `requirements/business/BR-XXX.md`
   - Defines business objectives and acceptance criteria
   - No parent requirements

2. **System Requirements (SR)** - *How the system should work*
   - Location: `requirements/system/SR-XXX.md`
   - Derives from business requirements
   - System-level capabilities and interfaces

3. **Software Requirements (TR)** - *Technical implementation*
   - Location: `requirements/software/TR-XXX.md`
   - Derives from system requirements
   - Code-level design decisions

4. **Test Requirements (TRQ)** - *What to test*
   - Location: `verification/requirements/TRQ-XXX.md`
   - Verifies system/software requirements
   - Defines test scope and success criteria

5. **Test Cases (TC)** - *How to test*
   - Location: `verification/test-cases/TC-XXX.md`
   - Tests specific test requirements
   - Executable test procedures with results

## Creating New Requirements

### Using Templates

```bash
# Business requirement
cp requirements/templates/BR-XXX.md requirements/business/BR-003.md

# System requirement
cp requirements/templates/SR-XXX.md requirements/system/SR-006.md

# Software requirement
cp requirements/templates/TR-XXX.md requirements/software/TR-010.md

# Test requirement
cp verification/templates/TRQ-XXX.md verification/requirements/TRQ-006.md

# Test case
cp verification/templates/TC-XXX.md verification/test-cases/TC-006.md
```

### Requirement Format

All requirements use Markdown with YAML front matter:

```yaml
---
id: SR-001
title: User Authentication
level: system
status: approved
priority: high
owner: Security Team
version: 1.0
created: 2025-12-31
last_updated: 2025-12-31
links:
  derives: [BR-001]
  satisfies: [TR-001, TR-002]
  depends_on: []
  verified_by: [TRQ-001]
---

# SR-001: User Authentication

## Description
The system shall provide secure user authentication...

## Acceptance Criteria
1. Users can log in with username/password
2. Failed attempts are logged
3. Session timeout after 30 minutes
```

## Linking Requirements

### Link Types

| Link Type | Direction | Purpose |
|-----------|-----------|---------|
| `derives` | Child → Parent | Lower-level derives from higher-level |
| `satisfies` | Child → Parent | Implementation satisfies requirement |
| `depends_on` | Peer → Peer | Implementation dependencies |
| `verified_by` | Req → TRQ | Requirement verified by test requirement |
| `tests` | TC → TRQ | Test case implements test requirement |

### Example Link Flow

```yaml
# BR-001 (Business)
links:
  verified_by: []

# SR-001 (System)
links:
  derives: [BR-001]
  verified_by: [TRQ-001]

# TR-001 (Software)
links:
  derives: [SR-001]
  verified_by: [TRQ-001]

# TRQ-001 (Test Requirement)
links:
  verifies: [SR-001, TR-001]
  tested_by: [TC-001]

# TC-001 (Test Case)
links:
  tests: [TRQ-001]
```

## Validation and Quality

### Validate Requirements

```bash
# Build traceability database
docker run --rm -v "$(pwd):/workspace" -w /workspace \
    req-formatter "python tools/build_traceability.py"

# Validate structure and links
docker run --rm -v "$(pwd):/workspace" -w /workspace \
    req-formatter "python tools/validate_requirements.py"
```

Validates:
- ✅ Required fields present
- ✅ Valid status and priority values
- ✅ All link targets exist
- ✅ No circular dependencies
- ✅ Unique requirement IDs
- ✅ Valid YAML front matter

### Code Quality (for developers)

All Python tools maintain **10/10 quality score**:

```bash
# Build formatter image (one-time)
docker build -f Dockerfile.formatter -t req-formatter .

# Format code
bash scripts/format.sh

# Run all quality checks
bash scripts/docker-quality-checks.sh
```

Quality standards:
- ✅ **pylint**: 10.00/10
- ✅ **black**: Consistent formatting
- ✅ **isort**: Sorted imports
- ✅ **flake8**: Style guide compliance
- ✅ **mypy**: Type checking

See [DOCKER_TOOLS.md](DOCKER_TOOLS.md) for detailed Docker usage.

## Workflow Example

### Complete Workflow: Adding a New Feature

```bash
# 1. Create business requirement
cp requirements/templates/BR-XXX.md requirements/business/BR-003.md
# Edit: Define business need and acceptance criteria

# 2. Create system requirements
cp requirements/templates/SR-XXX.md requirements/system/SR-006.md
# Edit: Set links.derives: [BR-003]
# Define system-level behavior

# 3. Create software requirements  
cp requirements/templates/TR-XXX.md requirements/software/TR-010.md
# Edit: Set links.derives: [SR-006]
# Define technical implementation

# 4. Create test requirements
cp verification/templates/TRQ-XXX.md verification/requirements/TRQ-006.md
# Edit: Set links.verifies: [SR-006, TR-010]
# Define what needs to be tested

# 5. Create test cases
cp verification/templates/TC-XXX.md verification/test-cases/TC-006.md
# Edit: Set links.tests: [TRQ-006]
# Write test procedures

# 6. Generate traceability
bash scripts/run-toolkit-with-docker.sh

# 7. Review reports
open outputs/traceability_expandable.html

# 8. Commit
git add .
git commit -m "feat: Add new authentication feature with tests"
```

## Generated Reports

### HTML Reports

- **traceability.html** - Complete matrix with all requirements and links
- **traceability_expandable.html** - Interactive view with expandable business requirements

### CSV Export

- **traceability.csv** - Import into Excel/Google Sheets for analysis

### Graphviz Diagram

```bash
# Generate and view diagram
bash scripts/run-toolkit-with-docker.sh
dot -Tpng outputs/requirements.dot -o outputs/requirements.png
```

Color coding:
- 🟦 **Blue**: Business requirements
- 🟩 **Green**: System requirements  
- 🟨 **Yellow**: Software requirements
- 🟧 **Orange**: Test requirements
- 🟥 **Red**: Test cases

## Development

### Architecture

The tools follow DRY principles:
- **common.py** - Shared utilities used by all tools
  - `load_trace()` - Load traceability database
  - `extract_link_targets()` - Parse link relationships
  - `iter_requirement_files()` - File iteration

All export tools import from `common.py` to avoid code duplication.

### Adding New Export Formats

1. Create `tools/export_myformat.py`
2. Import from `common.py`
3. Implement your export logic
4. Add to `scripts/run-toolkit-with-docker.sh`

### Running Tools Individually

```bash
# Build traceability
docker run --rm -v "$(pwd):/workspace" -w /workspace \
    req-formatter "python tools/build_traceability.py"

# Validate
docker run --rm -v "$(pwd):/workspace" -w /workspace \
    req-formatter "python tools/validate_requirements.py"

# Export HTML
docker run --rm -v "$(pwd):/workspace" -w /workspace \
    req-formatter "python tools/export_html_expandable.py"
```

## Documentation

- **[DOCKER_TOOLS.md](DOCKER_TOOLS.md)** - Docker-based development setup
- **[docs/requirements-model.md](docs/requirements-model.md)** - Requirement model details
- **[docs/conventions.md](docs/conventions.md)** - Naming conventions
- **[docs/traceability.md](docs/traceability.md)** - Traceability tracking explained
- **[docs/code-quality-improvements.md](docs/code-quality-improvements.md)** - Quality journey

## Tips for Success

### Requirements
- ✅ Use clear, measurable acceptance criteria
- ✅ Keep requirements atomic (single responsibility)
- ✅ Always link to parent requirements
- ✅ Update `last_updated` when making changes
- ✅ Use sequential IDs within each level
- ❌ Don't create orphaned requirements
- ❌ Don't skip requirement levels

### Test Cases
- ✅ Write reproducible test steps
- ✅ Document preconditions clearly
- ✅ Record actual results after execution
- ✅ Reference test evidence (logs, screenshots)
- ✅ Update execution status regularly

### Version Control
- ✅ Commit related changes together
- ✅ Use descriptive commit messages
- ✅ Regenerate reports before committing
- ✅ Review traceability in pull requests

## Troubleshooting

### "Missing trace.json" Error

Run traceability build first:
```bash
docker run --rm -v "$(pwd):/workspace" -w /workspace \
    req-formatter "python tools/build_traceability.py"
```

### Validation Errors

Check that:
- All requirement IDs are unique
- All link targets exist in the repository
- YAML front matter is valid
- Required fields are present

### Broken Links in Reports

Regenerate everything:
```bash
bash scripts/run-toolkit-with-docker.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks: `bash scripts/docker-quality-checks.sh`
5. Commit with descriptive message
6. Create pull request

See [DOCKER_TOOLS.md](DOCKER_TOOLS.md) for development setup.

## License

[Add your license here]

## Authors

- [Add author information]

---

**🚀 Built with Python, Docker, Markdown, and Git for modern requirements management.**
