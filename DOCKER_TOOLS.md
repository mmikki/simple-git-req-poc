# Docker-Based Development Tools

All Python quality tools run in Docker - no need to install anything on your host!

## Quick Start

### 1. Build the formatter image (one-time)
```bash
docker build -f Dockerfile.formatter -t req-formatter .
```

### 2. Format your code
```bash
bash scripts/format.sh
```

### 3. Run quality checks
```bash
bash scripts/docker-quality-checks.sh
```

### 4. Run individual tools
```bash
# Format specific file
bash scripts/format.sh tools/export_html.py

# Check only (no changes)
docker run --rm -v "$(pwd):/workspace" req-formatter "black tools/ --check"

# Run any Python tool
docker run --rm -v "$(pwd):/workspace" -w /workspace req-formatter \
    "python tools/build_traceability.py"
```

## What's Included

- **black** - Code formatter
- **isort** - Import sorter
- **flake8** - Style checker
- **pylint** - Code quality analyzer
- **mypy** - Type checker
- **pyyaml** - YAML parsing (for tools)

## Benefits

✅ No Python installation needed on host
✅ Consistent tool versions
✅ Clean host machine
✅ Easy CI/CD integration
✅ Works on any OS with Docker

## CI/CD Integration

Add to `.github/workflows/quality.yml`:
```yaml
- name: Run quality checks
  run: |
    docker build -f Dockerfile.formatter -t req-formatter .
    bash scripts/docker-quality-checks.sh
```
