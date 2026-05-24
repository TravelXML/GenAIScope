# Installation

## System Requirements

- Python 3.11 or higher
- pip or poetry package manager
- Optional: API keys for providers (OpenAI, Anthropic, Google)

## Basic Installation

### Using pip

```bash
pip install genaiscope
```

### Using poetry

```bash
poetry add genaiscope
```

## Optional Dependencies

GenAIScope is designed with minimal dependencies. Install optional packages for specific features:

### For OpenAI Support

```bash
pip install genaiscope[openai]
```

Requires: `openai>=1.0.0`

### For Anthropic Support

```bash
pip install genaiscope[anthropic]
```

Requires: `anthropic>=0.7.0`

### For Google Gemini Support

```bash
pip install genaiscope[google]
```

Requires: `google-generativeai>=0.3.0`

### For Development

```bash
pip install genaiscope[dev]
```

Includes: pytest, black, ruff, mypy

### For Documentation

```bash
pip install genaiscope[docs]
```

Includes: mkdocs, mkdocs-material

### Everything

```bash
pip install genaiscope[all]
```

## Verify Installation

```bash
python -c "import genaiscope; print(genaiscope.__version__)"
```

Or use the CLI:

```bash
genaiscope version
```

## Virtual Environment Setup (Recommended)

### Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows

# Install GenAIScope
pip install genaiscope
```

### Using conda

```bash
# Create environment
conda create -n genaiscope python=3.11

# Activate
conda activate genaiscope

# Install GenAIScope
pip install genaiscope
```

## Development Installation

For contributing to GenAIScope:

```bash
# Clone repository
git clone https://github.com/genaiscope/genaiscope.git
cd genaiscope

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in editable mode with all dependencies
pip install -e ".[dev,docs]"

# Run tests
pytest tests/
```

## Configuration

### Using Environment Variables

Create a `.env` file:

```bash
GENAISCOPE_PROVIDER=openai
OPENAI_API_KEY=sk-...
GENAISCOPE_MODEL=gpt-4
```

Or set in your shell:

```bash
export OPENAI_API_KEY=sk-...
```

### Using Python API

```python
from genaiscope.core.config import Config, set_config

config = Config(
    provider="openai",
    openai_api_key="sk-...",
    model="gpt-4",
)
set_config(config)
```

## Troubleshooting

### ImportError: No module named 'genaiscope'

Make sure GenAIScope is installed:

```bash
pip install genaiscope
```

And you're using the correct Python environment.

### API Key Errors

Ensure your API key is set:

```bash
export OPENAI_API_KEY=sk-...
# or set in .env file
```

### Permission Errors

On Linux/Mac, you may need to use `sudo`:

```bash
sudo pip install genaiscope
```

Or better yet, use a virtual environment (see above).

## Next Steps

- Read [Quick Start](quickstart.md)
- Learn [Concepts](concepts.md)
- Try [Recipes](recipes/prompt-inspection.md)
