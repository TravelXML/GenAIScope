# Contributing to GenAIScope

Thank you for your interest in contributing to GenAIScope! We welcome contributions from everyone.

## Code of Conduct

Please be respectful and inclusive in all interactions. See CODE_OF_CONDUCT.md for details.

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported
- Provide a clear, detailed description
- Include reproduction steps
- Share your environment details

### Suggesting Enhancements

- Check if the suggestion has already been made
- Provide clear use cases
- Explain why the feature would be useful
- Suggest implementation approach if possible

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Add or update tests
5. Run tests and linting
6. Commit with clear messages
7. Push to your fork
8. Create a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/genaiscope/genaiscope.git
cd genaiscope

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev,docs]"
```

## Code Standards

- Use Python 3.11+
- Follow PEP 8 style guide
- Use type hints
- Write clear docstrings
- Keep lines under 100 characters

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/genaiscope

# Run specific test
pytest tests/test_models.py::test_scope_config_default
```

## Linting and Formatting

```bash
# Check with ruff
ruff check src/

# Format with black
black src/ tests/

# Check types with mypy
mypy src/
```

## Documentation

- Update docs/ for user-facing changes
- Update docstrings for API changes
- Run `mkdocs serve` to preview

## Commit Messages

- Use clear, descriptive messages
- Start with a verb (Add, Fix, Update, etc.)
- Reference issues when relevant
- Example: "Add PII detection for phone numbers (#123)"

## Pull Request Process

1. Update README if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Request review from maintainers
5. Address feedback promptly

## Questions?

- Open a discussion on GitHub
- Check existing documentation
- Review similar code in the codebase

Thank you for contributing to GenAIScope!
