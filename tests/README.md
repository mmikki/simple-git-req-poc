# Unit Tests

Comprehensive unit tests for all Python tools.

## Running Tests

### Using Docker (recommended)

```bash
# Run all tests
bash scripts/run-tests.sh

# Run with coverage report
bash scripts/run-tests.sh --cov-report=html

# Run specific test file
bash scripts/run-tests.sh tests/test_common.py

# Run specific test
bash scripts/run-tests.sh tests/test_common.py::TestLoadTrace::test_load_trace_success
```

### Using Virtual Environment

```bash
# Activate venv
source .venv/bin/activate

# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=tools --cov-report=html
```

## Test Structure

```
tests/
├── __init__.py
├── test_common.py              # Tests for common.py utilities
├── test_validate_requirements.py  # Tests for validation logic
└── README.md                    # This file
```

## Test Coverage

Current coverage:

| Module | Coverage | Notes |
|--------|----------|-------|
| common.py | 100% | All shared utilities tested |
| validate_requirements.py | 85% | Core validation tested |

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<FunctionOrClass>`
- Test methods: `test_<what_it_tests>`

### Example Test

```python
class TestMyFunction:
    """Tests for my_function()."""

    def test_valid_input(self):
        """Test with valid input."""
        result = my_function("valid")
        assert result == "expected"

    def test_invalid_input(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            my_function("invalid")
```

### Using Fixtures

```python
import pytest

@pytest.fixture
def sample_data(tmp_path):
    """Create sample test data."""
    file_path = tmp_path / "test.json"
    file_path.write_text('{"key": "value"}')
    return file_path

def test_with_fixture(sample_data):
    """Test using fixture."""
    assert sample_data.exists()
```

## Best Practices

✅ **DO:**
- Test one thing per test method
- Use descriptive test names
- Test both success and failure cases
- Use fixtures for common setup
- Mock external dependencies
- Keep tests fast

❌ **DON'T:**
- Test multiple things in one test
- Depend on test execution order
- Use real files/network in unit tests
- Skip error cases
- Write tests without assertions

## CI Integration

Tests run automatically in CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    docker build -f Dockerfile.formatter -t req-formatter .
    bash scripts/run-tests.sh
```

## Coverage Reports

After running tests with coverage:

```bash
# View HTML report
open htmlcov/index.html

# View terminal report
pytest tests/ --cov=tools --cov-report=term-missing
```

## Debugging Tests

```bash
# Run with print statements visible
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Enter debugger on failure
pytest tests/ --pdb
```

## Quick Start

### Prerequisites
- Docker
- Git

### One-time Setup: Build the Docker Image

```bash
# Build the toolkit image (do this once, or after updating tools)
bash scripts/build-docker-image.sh
```

### Generate Traceability Reports

```bash
# Run on current directory
bash scripts/run-reqs-toolkit.sh

# Or use the convenience script (builds if needed)
bash scripts/run-toolkit-with-docker.sh
```

### Run on Different Projects

```bash
# Build the image once in this repo
cd /path/to/simple-git-req-poc
bash scripts/build-docker-image.sh

# Use it on any project with requirements
cd /path/to/project-a
bash /path/to/simple-git-req-poc/scripts/run-reqs-toolkit.sh

cd /path/to/project-b
bash /path/to/simple-git-req-poc/scripts/run-reqs-toolkit.sh
```
