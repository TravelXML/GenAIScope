# Cost Analysis Recipe

Learn how to estimate and control API costs for GenAI applications.

## Basic Cost Estimation

```python
from genaiscope.analyzers import CostAnalyzer

analyzer = CostAnalyzer()

# Estimate cost for a single API call
costs = analyzer.estimate_cost(
    model="gpt-4",
    input_tokens=100,
    output_tokens=150
)

print(f"Input cost: ${costs['input_cost']:.4f}")
print(f"Output cost: ${costs['output_cost']:.4f}")
print(f"Total cost: ${costs['total_cost']:.4f}")
```

## Supported Models and Pricing

```python
from genaiscope.analyzers import CostAnalyzer

analyzer = CostAnalyzer()

# Google Gemini - cheapest
gemini_costs = analyzer.estimate_cost("gemini-pro", 1000, 1000)

# OpenAI GPT-3.5 - budget friendly
gpt35_costs = analyzer.estimate_cost("gpt-3.5-turbo", 1000, 1000)

# Anthropic Claude 3 Sonnet - balanced
sonnet_costs = analyzer.estimate_cost("claude-3-sonnet", 1000, 1000)

# Anthropic Claude 3 Opus - most expensive
opus_costs = analyzer.estimate_cost("claude-3-opus", 1000, 1000)

# OpenAI GPT-4 - premium
gpt4_costs = analyzer.estimate_cost("gpt-4", 1000, 1000)

print("Model\tInput\t\tOutput\t\tTotal")
for name, costs in [
    ("Gemini", gemini_costs),
    ("GPT-3.5", gpt35_costs),
    ("Claude Sonnet", sonnet_costs),
    ("Claude Opus", opus_costs),
    ("GPT-4", gpt4_costs),
]:
    print(f"{name}\t${costs['input_cost']:.4f}\t${costs['output_cost']:.4f}\t${costs['total_cost']:.4f}")
```

## Cost Tracking in Production

```python
from genaiscope.analyzers import CostAnalyzer
import json
from datetime import datetime

class CostTracker:
    def __init__(self):
        self.analyzer = CostAnalyzer()
        self.costs = []
        self.total_cost = 0.0
    
    def track_call(self, model: str, input_tokens: int, output_tokens: int):
        """Track an API call cost."""
        costs = self.analyzer.estimate_cost(model, input_tokens, output_tokens)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": costs['input_cost'],
            "output_cost": costs['output_cost'],
            "total_cost": costs['total_cost'],
        }
        
        self.costs.append(entry)
        self.total_cost += costs['total_cost']
        
        return costs['total_cost']
    
    def get_summary(self):
        """Get cost summary."""
        return {
            "total_cost": self.total_cost,
            "call_count": len(self.costs),
            "average_cost": self.total_cost / len(self.costs) if self.costs else 0,
            "calls": self.costs,
        }
    
    def save_to_file(self, filename: str):
        """Save cost data to file."""
        with open(filename, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)

# Usage
tracker = CostTracker()

# Track API calls
tracker.track_call("gpt-4", 100, 200)
tracker.track_call("gpt-3.5-turbo", 50, 100)

# Get summary
summary = tracker.get_summary()
print(f"Total cost: ${summary['total_cost']:.4f}")
print(f"Calls: {summary['call_count']}")

# Save for analysis
tracker.save_to_file("costs.json")
```

## Cost Optimization Strategies

### 1. Model Selection

```python
from genaiscope.analyzers import CostAnalyzer

analyzer = CostAnalyzer()

def find_cheapest_model(input_tokens, output_tokens):
    """Find cheapest model for your needs."""
    models = {
        "gpt-3.5-turbo": "OpenAI",
        "gemini-pro": "Google",
        "claude-3-sonnet": "Anthropic",
    }
    
    costs = {}
    for model in models:
        result = analyzer.estimate_cost(model, input_tokens, output_tokens)
        costs[model] = result['total_cost']
    
    cheapest = min(costs, key=costs.get)
    print(f"Cheapest: {cheapest} at ${costs[cheapest]:.4f}")
    return cheapest

find_cheapest_model(1000, 1000)
```

### 2. Batch Processing

```python
from genaiscope.analyzers import CostAnalyzer

analyzer = CostAnalyzer()

def compare_batch_vs_individual(items):
    """Compare batch vs individual processing costs."""
    
    # Individual: 10 items @ 100 input, 150 output each
    individual_cost = 0
    for _ in items:
        costs = analyzer.estimate_cost("gpt-4", 100, 150)
        individual_cost += costs['total_cost']
    
    # Batch: 1 call with combined tokens (rough estimate)
    batch_input = 100 * len(items)
    batch_output = 150 * len(items)
    batch_costs = analyzer.estimate_cost("gpt-4", batch_input, batch_output)
    batch_cost = batch_costs['total_cost']
    
    savings = individual_cost - batch_cost
    savings_pct = (savings / individual_cost) * 100
    
    print(f"Individual: ${individual_cost:.4f}")
    print(f"Batch: ${batch_cost:.4f}")
    print(f"Savings: ${savings:.4f} ({savings_pct:.1f}%)")
```

### 3. Token Optimization

```python
from genaiscope.analyzers import CostAnalyzer

analyzer = CostAnalyzer()

# Compare costs with different approaches
def optimize_tokens():
    # Verbose approach
    verbose_costs = analyzer.estimate_cost("gpt-4", 300, 500)
    
    # Concise approach
    concise_costs = analyzer.estimate_cost("gpt-4", 150, 250)
    
    savings = verbose_costs['total_cost'] - concise_costs['total_cost']
    
    print(f"Verbose: ${verbose_costs['total_cost']:.4f}")
    print(f"Concise: ${concise_costs['total_cost']:.4f}")
    print(f"Savings: ${savings:.4f}")

optimize_tokens()
```

## Budget Monitoring

```python
from genaiscope.analyzers import CostAnalyzer

class BudgetMonitor:
    def __init__(self, monthly_budget: float):
        self.analyzer = CostAnalyzer()
        self.monthly_budget = monthly_budget
        self.spent = 0.0
        self.calls = []
    
    def can_make_call(self, model: str, input_tokens: int, output_tokens: int) -> bool:
        """Check if budget allows another call."""
        costs = self.analyzer.estimate_cost(model, input_tokens, output_tokens)
        call_cost = costs['total_cost']
        
        if self.spent + call_cost > self.monthly_budget:
            remaining = self.monthly_budget - self.spent
            print(f"Budget exceeded! Remaining: ${remaining:.4f}")
            return False
        
        return True
    
    def make_call(self, model: str, input_tokens: int, output_tokens: int):
        """Record a call if budget allows."""
        if not self.can_make_call(model, input_tokens, output_tokens):
            raise ValueError("Insufficient budget")
        
        costs = self.analyzer.estimate_cost(model, input_tokens, output_tokens)
        call_cost = costs['total_cost']
        
        self.spent += call_cost
        self.calls.append({
            "model": model,
            "cost": call_cost,
            "running_total": self.spent,
        })
        
        return call_cost
    
    def get_status(self):
        """Get budget status."""
        remaining = self.monthly_budget - self.spent
        usage_pct = (self.spent / self.monthly_budget) * 100
        
        return {
            "budget": self.monthly_budget,
            "spent": self.spent,
            "remaining": remaining,
            "usage_percent": usage_pct,
            "calls_made": len(self.calls),
        }

# Usage
monitor = BudgetMonitor(monthly_budget=100.0)

try:
    cost = monitor.make_call("gpt-4", 100, 200)
    print(f"Call cost: ${cost:.4f}")
    
    status = monitor.get_status()
    print(f"Budget status: {status['usage_percent']:.1f}% used")
except ValueError as e:
    print(f"Cannot make call: {e}")
```

## CLI Usage

```bash
# Estimate single call cost
genaiscope estimate-cost gpt-4 100 200

# Create a script to track costs
cat > track_costs.py << 'EOF'
from genaiscope.analyzers import CostAnalyzer

analyzer = CostAnalyzer()
models = ["gpt-4", "gpt-3.5-turbo", "gemini-pro"]

print("Cost comparison for 1000 input + 1000 output tokens:")
for model in models:
    costs = analyzer.estimate_cost(model, 1000, 1000)
    print(f"{model}: ${costs['total_cost']:.4f}")
EOF

python track_costs.py
```

## Testing Cost Calculations

```python
import pytest
from genaiscope.analyzers import CostAnalyzer

def test_cost_estimation():
    """Test cost estimation accuracy."""
    analyzer = CostAnalyzer()
    
    costs = analyzer.estimate_cost("gpt-4", 100, 200)
    
    # GPT-4: $0.03/1K input, $0.06/1K output
    expected_input = 0.003
    expected_output = 0.012
    expected_total = 0.015
    
    assert abs(costs['input_cost'] - expected_input) < 0.0001
    assert abs(costs['output_cost'] - expected_output) < 0.0001
    assert abs(costs['total_cost'] - expected_total) < 0.0001

def test_budget_monitoring():
    """Test budget monitoring."""
    from genaiscope.analyzers import CostAnalyzer
    
    class MockBudgetMonitor:
        def __init__(self, budget):
            self.budget = budget
            self.spent = 0
        
        def can_afford(self, cost):
            return self.spent + cost <= self.budget
    
    monitor = MockBudgetMonitor(100.0)
    assert monitor.can_afford(50.0)
    assert monitor.can_afford(50.0)
    assert not monitor.can_afford(1.0)
```

## Pricing Update Warning

**Note**: Pricing changes frequently. Check the official documentation:
- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [Google Gemini Pricing](https://ai.google.dev/pricing)

## Next Steps

- Try [PII Redaction](pii-redaction.md)
- Learn [RAG Inspection](rag-inspection.md)
- See [Structured Output Validation](structured-output.md)
