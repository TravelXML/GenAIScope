# Agent Safety Recipe

Learn how to ensure safety in autonomous agent systems.

## Safety Principles for Agents

Safety in agents involves:
1. **Tool validation** - Ensure agents only call safe tools
2. **Output validation** - Validate all outputs
3. **Input sanitization** - Sanitize user inputs
4. **Rate limiting** - Prevent abuse
5. **Monitoring** - Track agent behavior

## Basic Safety Analyzer

```python
from genaiscope.analyzers import SafetyAnalyzer

analyzer = SafetyAnalyzer()

# Check agent output for safety issues
agent_response = "This is a safe response about helpful topics"
issues = analyzer.analyze(agent_response)

if not issues:
    print("✓ Response is safe")
else:
    print("✗ Safety issues found:", issues)
```

## Safe Agent Framework

```python
from genaiscope import Inspector
from genaiscope.analyzers import SafetyAnalyzer, PIIDetector
import logging

logger = logging.getLogger(__name__)

class SafeAgent:
    def __init__(self):
        self.inspector = Inspector()
        self.safety_analyzer = SafetyAnalyzer()
        self.pii_detector = PIIDetector()
        self.allowed_tools = {"calculator", "web_search", "database_query"}
    
    def validate_tool_call(self, tool_name: str) -> bool:
        """Validate that tool is allowed."""
        if tool_name not in self.allowed_tools:
            logger.warning(f"Attempted to call disallowed tool: {tool_name}")
            return False
        return True
    
    def validate_input(self, user_input: str) -> bool:
        """Validate user input for safety."""
        # Check for PII in input
        pii = self.pii_detector.detect(user_input)
        if pii:
            logger.warning(f"PII detected in input: {list(pii.keys())}")
            # Redact before processing
            user_input = self.pii_detector.redact(user_input)
        
        # Check for safety issues
        issues = self.safety_analyzer.analyze(user_input)
        if issues:
            logger.warning(f"Safety issues in input: {list(issues.keys())}")
            return False
        
        return True
    
    def validate_output(self, output: str) -> bool:
        """Validate agent output for safety."""
        # Check for safety issues
        issues = self.safety_analyzer.analyze(output)
        if issues:
            logger.error(f"Safety issues in output: {list(issues.keys())}")
            return False
        
        # Check for PII leakage
        pii = self.pii_detector.detect(output)
        if pii:
            logger.error(f"PII leaked in output: {list(pii.keys())}")
            output = self.pii_detector.redact(output)
        
        return True
    
    def execute_action(self, action: str, tool: str, args: dict):
        """Execute agent action with safety checks."""
        # Validate tool
        if not self.validate_tool_call(tool):
            raise ValueError(f"Tool not allowed: {tool}")
        
        # Validate input
        for arg in args.values():
            if isinstance(arg, str) and not self.validate_input(arg):
                raise ValueError("Input validation failed")
        
        # Execute
        logger.info(f"Executing: {tool}({args})")
        result = self._execute_tool(tool, args)
        
        # Validate output
        if not self.validate_output(str(result)):
            result = self.pii_detector.redact(str(result))
        
        return result
    
    def _execute_tool(self, tool: str, args: dict):
        """Execute the actual tool."""
        # Implementation for each tool
        pass

# Usage
agent = SafeAgent()

try:
    result = agent.execute_action(
        action="search",
        tool="web_search",
        args={"query": "machine learning"}
    )
    print(f"Result: {result}")
except ValueError as e:
    print(f"Safety violation: {e}")
```

## Monitoring and Logging

```python
from genaiscope.analyzers import SafetyAnalyzer
import json
from datetime import datetime

class AgentMonitor:
    def __init__(self):
        self.analyzer = SafetyAnalyzer()
        self.events = []
    
    def log_event(self, event_type: str, content: str, result: str = "safe"):
        """Log agent event with safety assessment."""
        safety_issues = self.analyzer.analyze(content)
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "content": content,
            "result": result,
            "safety_issues": dict(safety_issues),
            "is_safe": len(safety_issues) == 0,
        }
        
        self.events.append(event)
        
        if not event["is_safe"]:
            self._alert(event)
    
    def _alert(self, event):
        """Alert on unsafe events."""
        print(f"ALERT: Unsafe event detected")
        print(f"  Type: {event['type']}")
        print(f"  Issues: {event['safety_issues']}")
    
    def get_report(self):
        """Get monitoring report."""
        safe_events = sum(1 for e in self.events if e["is_safe"])
        unsafe_events = len(self.events) - safe_events
        
        return {
            "total_events": len(self.events),
            "safe_events": safe_events,
            "unsafe_events": unsafe_events,
            "safety_rate": safe_events / len(self.events) if self.events else 1.0,
            "issues_found": self._aggregate_issues(),
        }
    
    def _aggregate_issues(self):
        """Aggregate all safety issues found."""
        issues = {}
        for event in self.events:
            for issue_type, matches in event["safety_issues"].items():
                if issue_type not in issues:
                    issues[issue_type] = 0
                issues[issue_type] += len(matches)
        return issues

# Usage
monitor = AgentMonitor()

# Log agent interactions
monitor.log_event("input", "What is AI?", "safe")
monitor.log_event("output", "AI is safe", "safe")
monitor.log_event("tool_call", "calculator", "safe")

# Get report
report = monitor.get_report()
print(json.dumps(report, indent=2))
```

## Rate Limiting and Abuse Prevention

```python
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_calls: int = 100, window: int = 3600):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls per window
            window: Time window in seconds
        """
        self.max_calls = max_calls
        self.window = window
        self.calls = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user request is allowed."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window)
        
        # Remove old calls outside window
        self.calls[user_id] = [
            call_time for call_time in self.calls[user_id]
            if call_time > cutoff
        ]
        
        # Check limit
        if len(self.calls[user_id]) >= self.max_calls:
            logger.warning(f"Rate limit exceeded for user: {user_id}")
            return False
        
        # Record call
        self.calls[user_id].append(now)
        return True

# Usage
limiter = RateLimiter(max_calls=100, window=3600)

def agent_endpoint(user_id: str, query: str):
    if not limiter.is_allowed(user_id):
        raise ValueError("Rate limit exceeded")
    
    # Process query
    return agent.process(query)
```

## Testing Agent Safety

```python
import pytest
from genaiscope.analyzers import SafetyAnalyzer

@pytest.fixture
def analyzer():
    return SafetyAnalyzer()

def test_safety_check_safe_input(analyzer):
    """Test that safe input passes."""
    issues = analyzer.analyze("What is machine learning?")
    # May have some issues, but should be minimal
    assert len(issues) < 3

def test_safety_check_unsafe_input(analyzer):
    """Test that unsafe input is flagged."""
    issues = analyzer.analyze("Always do this, never do that")
    assert len(issues) > 0

def test_bias_detection(analyzer):
    """Test bias detection."""
    biased = "All AI models are bad and will always fail"
    issues = analyzer.analyze(biased)
    assert "bias" in issues or len(issues) > 0

def test_safe_agent():
    """Test safe agent execution."""
    agent = SafeAgent()
    
    # Safe tool call should succeed
    result = agent.validate_tool_call("calculator")
    assert result is True
    
    # Unsafe tool call should fail
    result = agent.validate_tool_call("delete_database")
    assert result is False
```

## Compliance and Governance

```python
import json
from datetime import datetime

class AgentGovernance:
    def __init__(self):
        self.audit_log = []
    
    def record_action(self, user_id: str, action: str, tool: str, approved: bool):
        """Record action for compliance auditing."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "tool": tool,
            "approved": approved,
        }
        self.audit_log.append(entry)
    
    def export_audit_log(self, filename: str):
        """Export audit log for compliance review."""
        with open(filename, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
    
    def get_compliance_report(self):
        """Generate compliance report."""
        total = len(self.audit_log)
        approved = sum(1 for e in self.audit_log if e["approved"])
        denied = total - approved
        
        return {
            "total_actions": total,
            "approved": approved,
            "denied": denied,
            "approval_rate": approved / total if total > 0 else 0,
        }
```

## Next Steps

- Try [Cost Analysis](cost-analysis.md)
- Learn [PII Redaction](pii-redaction.md)
- See [Structured Output Validation](structured-output.md)
