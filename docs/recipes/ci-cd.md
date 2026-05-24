# CI/CD Integration Recipe

Learn how to integrate GenAIScope into your CI/CD pipeline.

## GitHub Actions Integration

### Basic Validation Workflow

```yaml
# .github/workflows/genaiscope-validation.yml
name: GenAI Validation

on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  validate-genai:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install GenAIScope
        run: |
          pip install genaiscope
      
      - name: Validate Prompts
        run: |
          python scripts/validate_prompts.py
      
      - name: Check for PII
        run: |
          python scripts/check_pii.py
      
      - name: Estimate Costs
        run: |
          python scripts/estimate_costs.py
```

### Validation Script Example

```python
# scripts/validate_prompts.py
import sys
from genaiscope import Inspector
import glob

def validate_prompts():
    """Validate all prompt files in the repository."""
    inspector = Inspector()
    failed = 0
    
    # Find all prompt files
    prompt_files = glob.glob("prompts/**/*.txt", recursive=True)
    
    for prompt_file in prompt_files:
        with open(prompt_file, 'r') as f:
            prompt = f.read()
        
        report = inspector.inspect_prompt(prompt)
        
        # Check if all evaluations pass
        passes = sum(1 for e in report.evaluations if e.score > 0.7)
        total = len(report.evaluations)
        
        if passes < total:
            print(f"❌ {prompt_file}: {passes}/{total} checks passed")
            failed += 1
        else:
            print(f"✓ {prompt_file}: All checks passed")
    
    return failed

if __name__ == "__main__":
    failed = validate_prompts()
    sys.exit(failed)
```

## Pre-commit Hooks

### Setup Pre-commit

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: local
    hooks:
      - id: genaiscope-validate
        name: GenAIScope Validate
        entry: python scripts/pre_commit_check.py
        language: python
        stages: [commit]
        types: [text]
EOF

# Install hooks
pre-commit install
```

### Pre-commit Check Script

```python
# scripts/pre_commit_check.py
import sys
from genaiscope import Inspector
from genaiscope.analyzers import PIIDetector

def check_file(filename):
    """Check a file for issues."""
    with open(filename, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for PII
    pii_detector = PIIDetector()
    pii = pii_detector.detect(content)
    if pii:
        issues.append(f"PII detected: {list(pii.keys())}")
    
    # Check prompts for quality
    if "prompt" in filename.lower():
        inspector = Inspector()
        report = inspector.inspect_prompt(content)
        if any(e.score < 0.5 for e in report.evaluations):
            issues.append("Prompt quality too low")
    
    if issues:
        print(f"Issues in {filename}:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    exit_code = 0
    for filename in sys.argv[1:]:
        exit_code |= check_file(filename)
    sys.exit(exit_code)
```

## Test Integration

### Unit Tests with GenAIScope

```python
# tests/test_prompts.py
import pytest
from genaiscope import Inspector
from genaiscope.analyzers import PIIDetector

@pytest.fixture
def inspector():
    return Inspector()

@pytest.fixture
def pii_detector():
    return PIIDetector()

def test_system_prompt_quality(inspector):
    """Test system prompt meets quality standards."""
    with open("prompts/system.txt") as f:
        prompt = f.read()
    
    report = inspector.inspect_prompt(prompt)
    
    # All evaluations should pass
    assert all(e.score > 0.7 for e in report.evaluations)
    assert len(report.errors) == 0

def test_prompts_no_pii(pii_detector):
    """Test that prompts don't contain PII."""
    import glob
    
    for prompt_file in glob.glob("prompts/**/*.txt", recursive=True):
        with open(prompt_file) as f:
            content = f.read()
        
        pii = pii_detector.detect(content)
        assert not pii, f"PII found in {prompt_file}: {pii}"

def test_response_templates_valid(inspector):
    """Test response templates are properly formatted."""
    with open("templates/response.json") as f:
        template = f.read()
    
    report = inspector.inspect_output(template, expected_format="json")
    assert all(e.score > 0.7 for e in report.evaluations)
```

### Run Tests in CI

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=src/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Code Quality Checks

```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install ruff black mypy
      
      - name: Ruff
        run: ruff check src/ --format github
      
      - name: Black
        run: black --check src/
      
      - name: mypy
        run: mypy src/
```

## Production Deployment Checklist

```python
# scripts/pre_deployment_check.py
from genaiscope import Inspector
from genaiscope.analyzers import (
    PIIDetector,
    HallucinationDetector,
    SafetyAnalyzer,
)
import sys

class DeploymentChecklist:
    def __init__(self):
        self.inspector = Inspector()
        self.pii_detector = PIIDetector()
        self.hallucination_detector = HallucinationDetector()
        self.safety_analyzer = SafetyAnalyzer()
        self.checks_passed = 0
        self.checks_failed = 0
    
    def check_prompts(self, prompt_file):
        """Check prompts for production readiness."""
        with open(prompt_file) as f:
            prompt = f.read()
        
        report = self.inspector.inspect_prompt(prompt)
        
        if all(e.score > 0.8 for e in report.evaluations):
            print("✓ Prompt quality check passed")
            self.checks_passed += 1
        else:
            print("✗ Prompt quality check failed")
            self.checks_failed += 1
    
    def check_no_pii(self, content):
        """Ensure no PII in production data."""
        pii = self.pii_detector.detect(content)
        
        if not pii:
            print("✓ PII check passed")
            self.checks_passed += 1
        else:
            print("✗ PII found:", list(pii.keys()))
            self.checks_failed += 1
    
    def check_safety(self, content):
        """Check for safety issues."""
        issues = self.safety_analyzer.analyze(content)
        
        if not issues:
            print("✓ Safety check passed")
            self.checks_passed += 1
        else:
            print("✗ Safety issues found:", list(issues.keys()))
            self.checks_failed += 1
    
    def run_all_checks(self):
        """Run all deployment checks."""
        print("Running pre-deployment checks...\n")
        
        self.check_prompts("prompts/system.txt")
        self.check_prompts("prompts/user.txt")
        
        with open("config/config.json") as f:
            config = f.read()
        self.check_no_pii(config)
        self.check_safety(config)
        
        print(f"\nResults: {self.checks_passed} passed, {self.checks_failed} failed")
        return self.checks_failed == 0

if __name__ == "__main__":
    checker = DeploymentChecklist()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)
```

### Deployment Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install GenAIScope
        run: pip install genaiscope
      
      - name: Pre-deployment checks
        run: python scripts/pre_deployment_check.py
      
      - name: Run tests
        run: pytest tests/
      
      - name: Deploy
        run: python scripts/deploy.py
        env:
          DEPLOYMENT_TOKEN: ${{ secrets.DEPLOYMENT_TOKEN }}
```

## Cost Tracking in CI

```python
# scripts/track_costs.py
from genaiscope.analyzers import CostAnalyzer
import json

def track_api_costs():
    """Track API costs for CI/CD usage."""
    analyzer = CostAnalyzer()
    
    # Estimate costs for typical CI/CD work
    costs = {
        "prompt_validation": analyzer.estimate_cost("gpt-3.5-turbo", 500, 200),
        "unit_tests": analyzer.estimate_cost("gpt-3.5-turbo", 1000, 500),
        "deployment_check": analyzer.estimate_cost("gpt-3.5-turbo", 300, 100),
    }
    
    total_cost = sum(c['total_cost'] for c in costs.values())
    
    print(f"Estimated cost per run: ${total_cost:
