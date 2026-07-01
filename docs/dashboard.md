# Dashboard

Generate a static local HTML dashboard:

```bash
genaiscope dashboard generate
```

The default output path is `.genaiscope/reports/dashboard.html`.

## Sample

[`examples/dashboard_sample/dashboard.html`](https://github.com/TravelXML/GenAIScope/blob/main/examples/dashboard_sample/dashboard.html)
is a committed, browsable dashboard generated from a small demo dataset (memories, a prompt,
a file, and a few traces across OpenAI/Anthropic/Google). Regenerate it with:

```bash
python examples/dashboard_sample/populate_demo_data.py
```
