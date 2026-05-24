# Testing Guide for GenAIScope

This guide explains how to set up your environment and run all tests for GenAIScope.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git (for version control)

## Setup

### 1. Install the Project with Development Dependencies

```bash
# Clone or navigate to the GenAIScope directory
cd GenAIScope

# Create a virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package with all development dependencies
pip install -e ".[dev]"
```

This installs:
- Core dependencies: pydantic, typer, rich, aiohttp, python-dotenv
- Dev dependencies: pytest, black, ruff, mypy, mkdocs-material

### 2. Verify Installation

```bash
# Check Python version
python --version

# Verify imports work
python -c "import genaiscope; print(f'GenAIScope {genaiscope.__version__} installed')"

# Check CLI is available
genaiscope --help
```

## Running Tests

### Quick Test Run (All Tests)

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with summary
pytest tests/ --tb=short
```

### Test Individual Components

```bash
# Test core models
pytest tests/test_models.py -v

# Test analyzers
pytest tests/test_analyzers.py -v

# Test inspector
pytest tests/test_inspect.py -v

# Test scoring engine
pytest tests/test_scoring.py -v

# Test CLI
pytest tests/test_cli.py -v
```

### Run Tests with Coverage Report

```bash
# Generate coverage report
pytest tests/ --cov=src/genaiscope --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src/genaiscope --cov-report=html
# Open htmlcov/index.html in browser to view detailed report
```

### Run Specific Test

```bash
# Run a specific test file
pytest tests/test_analyzers.py::test_pii_detection -v

# Run tests matching a pattern
pytest -k "pii" -v
```

## Code Quality Checks

### 1. Format Code

```bash
# Format all Python files with black
black src/ tests/

# Format with custom line length
black src/ tests/ --line-length=100
```

### 2. Lint Code

```bash
# Check style and errors with ruff
ruff check src/ tests/

# Fix automatically fixable issues
ruff check --fix src/ tests/
```

### 3. Type Checking

```bash
# Type check with mypy
mypy src/genaiscope

# Strict type checking
mypy src/genaiscope --strict
```

### 4. Run All Quality Checks

```bash
# All in one
ruff check src/ tests/ && black --check src/ tests/ && mypy src/genaiscope && pytest tests/
```

## Manual Testing

### 1. Test Inspector API

```bash
# Start Python shell
python

# Run in Python:
from genaiscope import Inspector

inspector = Inspector()

# Test prompt inspection
report = inspector.inspect_prompt("What is machine learning?")
print(report.summary())

# Test output inspection  
report = inspector.inspect_output('{"name": "John", "age": 30}', "json")
print(report.summary())

# Exit
exit()
```

### 2. Test Analyzers

```bash
# Start Python shell
python

# Run in Python:
from genaiscope.analyzers import PIIDetector, CostAnalyzer

# Test PII detection
detector = PIIDetector()
pii_results = detector.detect("Contact me at john@example.com or 555-123-4567")
print(pii_results)

# Test PII redaction
redacted = detector.redact("Email john@example.com for more info")
print(redacted)

# Test cost analysis
analyzer = CostAnalyzer()
cost = analyzer.estimate_cost("gpt-4", 100, 50)
print(cost)

exit()
```

### 3. Test CLI Commands

```bash
# Show version
genaiscope version

# Show configuration
genaiscope config-show

# Inspect a prompt
genaiscope inspect-prompt "Is AI safe?" --output-format text

# Detect PII
genaiscope detect-pii "Email me at sarah@company.com" --redact

# Estimate costs
genaiscope estimate-cost gpt-4 1000 500

# Analyze text
genaiscope analyze-text "This is a test" --analyze-pii

# Validate JSON output
genaiscope validate-output '{"status": "success"}' --format json
```

### 4. Test Configuration

```bash
# Create .env file for custom configuration
cat > .env << EOF
GENAISCOPE_PROVIDER=openai
GENAISCOPE_MODEL=gpt-4
GENAISCOPE_TIMEOUT=30
EOF

# Run Python to test config loading
python -c "from genaiscope.core.config import get_config; print(get_config())"
```

## Testing Different Providers

### OpenAI Provider

```python
from genaiscope.core.config import set_config, ScopeConfig
from genaiscope.core.providers import get_provider

# Configure
config = ScopeConfig(provider="openai", api_key="sk-...")
set_config(config)

# Get provider instance
provider = get_provider("openai", "sk-...")
# provider.call() would make actual API calls
```

### Anthropic Provider

```python
from genaiscope.core.providers import get_provider

provider = get_provider("anthropic", "sk-ant-...")
```

### Local Provider (for testing without API keys)

```python
from genaiscope.core.providers import get_provider

def my_model(prompt):
    return "Test response"

provider = get_provider("local", model=my_model)
```

## Continuous Integration Testing

### GitHub Actions

Tests automatically run on:
- Every push to main/dev branches
- Every pull request
- Python 3.11 and 3.12

View results in `.github/workflows/tests.yml`

### Local Pre-Commit Testing

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run pre-commit checks before committing
pre-commit run --all-files
```

## Troubleshooting Tests

### Issue: "ModuleNotFoundError: No module named 'genaiscope'"

**Solution:**
```bash
pip install -e ".[dev]"  # Install in editable mode
```

### Issue: "pytest: command not found"

**Solution:**
```bash
pip install pytest pytest-cov
```

### Issue: "Tests fail with import errors"

**Solution:**
```bash
# Ensure you're in the correct directory
cd GenAIScope

# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows

# Reinstall dependencies
pip install -e ".[dev]"
```

### Issue: "API tests fail without credentials"

**Solution:**
Tests that require API keys use mocking. If you get errors:
1. Ensure `pytest-mock` is installed
2. Check test files have proper mocking setup
3. Set dummy API keys in `.env.test` if needed

```bash
# Skip tests requiring real API calls
pytest tests/ -m "not requires_api"
```

## Test Structure

```
tests/
├── test_models.py          # Tests for Pydantic models
├── test_analyzers.py       # Tests for analyzer classes
├── test_inspect.py         # Tests for Inspector API
├── test_scoring.py         # Tests for ScoringEngine
└── test_cli.py             # Tests for CLI commands

Key test coverage:
- ✅ Configuration loading and validation
- ✅ All analyzer functions (PII, cost, hallucination, etc.)
- ✅ Inspector methods (prompt, RAG, output)
- ✅ CLI command parsing and execution
- ✅ Error handling and edge cases
- ✅ Provider factory and instantiation
```

## Automated Testing Workflow

```bash
#!/bin/bash
# Save as run_tests.sh and run: chmod +x run_tests.sh && ./run_tests.sh

set -e  # Exit on first error

echo "🧪 Starting GenAIScope Test Suite..."
echo ""

# 1. Setup
echo "📦 Installing dependencies..."
pip install -e ".[dev]" > /dev/null 2>&1

# 2. Code quality
echo "✨ Checking code style..."
ruff check src/ tests/ > /dev/null 2>&1 && echo "✅ Ruff passed" || echo "❌ Ruff failed"

echo "🎨 Checking formatting..."
black --check src/ tests/ > /dev/null 2>&1 && echo "✅ Black passed" || echo "❌ Black failed"

echo "🔍 Type checking..."
mypy src/genaiscope > /dev/null 2>&1 && echo "✅ MyPy passed" || echo "❌ MyPy failed"

# 3. Run tests
echo ""
echo "🚀 Running unit tests..."
pytest tests/ -v --tb=short

# 4. Coverage
echo ""
echo "📊 Generating coverage report..."
pytest tests/ --cov=src/genaiscope --cov-report=term-missing

echo ""
echo "✅ ALL TESTS PASSED! 🎉"
```

## Testing Documentation

Build and test documentation locally:

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

Visit http://localhost:8000 to preview documentation.

## Performance Testing

For performance profiling:

```bash
# Profile PII detection
python -m cProfile -s cumulative -c "
from genaiscope.analyzers import PIIDetector
detector = PIIDetector()
for i in range(1000):
    detector.detect('test@example.com')
" | head -20

# Time cost analysis
import time
from genaiscope.analyzers import CostAnalyzer

start = time.time()
analyzer = CostAnalyzer()
for i in range(10000):
    analyzer.estimate_cost('gpt-4', 100, 50)
end = time.time()
print(f"Time: {end-start:.3f}s for 10000 calls")
```

## Next Steps After Testing

1. ✅ **All tests pass?** → Ready for development/deployment
2. ✅ **Want to contribute?** → See CONTRIBUTING.md
3. ✅ **Need to extend?** → Add custom analyzers to `src/genaiscope/analyzers.py`
4. ✅ **Ready for production?** → Deploy with the provided CI/CD workflow

---

**Questions?** Check [docs/](docs/) for detailed documentation or review [README.md](README.md).
