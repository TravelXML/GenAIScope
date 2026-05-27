# File Memory

File memory indexes TXT, MD, JSON, and CSV files into local document chunks.

```python
from genaiscope.files import FileMemory

files = FileMemory()
files.add_file("README.md")
print(files.search("installation"))
```
