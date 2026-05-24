# CLI Reference

## Installation

```bash
pip install genaiscope
```

All commands are available as `genaiscope <command>`.

## Global Options

Most commands support:
- `--help` - Show help message
- `--verbose` - Enable verbose output
- `--config` - Specify config file

## Commands

### version

Show GenAIScope version.

```bash
genaiscope version
```

Output:
```
GenAIScope version 0.1.0
```

### config-show

Display current configuration.

```bash
genaiscope config-show
```

Shows all settings from environment variables and configuration files.

### inspect-prompt

Inspect a prompt for quality and safety issues.

```bash
genaiscope inspect-prompt "Your prompt text here"
genaiscope inspect-prompt "What is AI?" --output-format json
```

**Options:**
- `--output-format` (text|json) - Output format (default: text)

### detect-pii

Detect Personally Identifiable Information.

```bash
# Detect and report
genaiscope detect-pii "My email is john@example.com"

# Detect and redact
genaiscope detect-pii "Email: john@example.com" --redact
```

**Options:**
- `--redact` - Output redacted version of text

**Detects:**
- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers
- IPv4 addresses

### estimate-cost

Calculate API costs.

```bash
genaiscope estimate-cost gpt-4 100 200
```

**Arguments:**
- `model` - Model name (e.g., gpt-4, gpt-3.5-turbo, claude-3-opus)
- `input_tokens` - Number of input tokens
- `output_tokens` - Number of output tokens

Output:
```
Cost Estimate for gpt-4
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Metric        ┃ Cost (USD) ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Input Cost    │ $0.0030    │
│ Output Cost   │ $0.0120    │
│ Total Cost    │ $0.0150    │
└───────────────┴────────────┘
```

### analyze-text

Comprehensive text analysis.

```bash
# Basic analysis
genaiscope analyze-text "Your text here"

# With PII detection
genaiscope analyze-text "Email: john@example.com" --analyze-pii

# With hallucination checking
genaiscope analyze-text "The sky is green" --analyze-hallucination --context "The sky is blue"

# All checks
genaiscope analyze-text "Your text" --analyze-pii --analyze-hallucination --context "reference text"
```

**Options:**
- `--analyze-pii` - Enable PII detection
- `--analyze-hallucination` - Enable hallucination detection
- `--context` - Reference context for hallucination checking

### validate-output

Validate structured output format.

```bash
# Validate JSON
genaiscope validate-output '{"name": "test"}' --format json

# Validate XML
genaiscope validate-output '<root></root>' --format xml

# Validate CSV
genaiscope validate-output 'name,age\nJohn,30' --format csv
```

**Options:**
- `--format` (json|xml|csv) - Expected format (default: json)

## Common Patterns

### Using in Scripts

```bash
#!/bin/bash

# Validate prompt before using
PROMPT="What is AI?"

if genaiscope inspect-prompt "$PROMPT"; then
    echo "Prompt is valid"
else
    echo "Prompt validation failed"
    exit 1
fi
```

### Piping Data

```bash
# Read from file and analyze
cat prompt.txt | xargs genaiscope inspect-prompt

# Process output from another command
GPT_RESPONSE=$(curl api.openai.com/...) 
genaiscope validate-output "$GPT_RESPONSE" --format json
```

### Cost Analysis Pipeline

```bash
# Estimate costs for batch operations
for MODEL in gpt-4 gpt-3.5-turbo; do
    genaiscope estimate-cost $MODEL 100 200
done
```

## Environment Variables

Configure with environment variables:

```bash
export GENAISCOPE_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export GENAISCOPE_MODEL=gpt-4
export GENAISCOPE_LOG_LEVEL=INFO
```

See [Configuration](../concepts.md#configuration) for all options.

## Exit Codes

- `0` - Success
- `1` - Error or validation failure
- `2` - Invalid command/arguments

## Output Formats

### Text (Default)

Human-readable output with formatting.

### JSON

Machine-readable output. Use with tools:

```bash
genaiscope inspect-prompt "test" --output-format json | jq .
```

## Troubleshooting

### Command not found

Ensure GenAIScope is installed:
```bash
pip install genaiscope
```

### API key errors

Set API key:
```bash
export OPENAI_API_KEY=sk-...
```

### Permission denied

On Linux/Mac, use `sudo` or activate virtual environment.

## See Also

- [Python API](../api-reference.md)
- [Quick Start](../quickstart.md)
- [Configuration](../concepts.md)
