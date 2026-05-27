# Local Tracing

Local tracing records model calls, latency, token counts, cost estimates, and errors.

```python
from genaiscope.tracing import LocalTracer

tracer = LocalTracer()
tracer.log(name="demo", input_text="hello", output_text="hi", model="local")
```
