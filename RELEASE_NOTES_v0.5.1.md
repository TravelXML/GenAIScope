# GenAIScope v0.5.1 Release Notes

This patch release fixes two crashes in the REST API server that affected every release
since it shipped in v0.4.0.

## Fixed

- **REST API route registration crash.** `create_app()` raised `PydanticUndefinedAnnotation`
  against current FastAPI/Pydantic releases because `routes_health.py`/`routes_memory.py`
  combined `from __future__ import annotations` with imports made inside the route-registration
  functions instead of at module level. Fixed by moving those imports to module scope.
- **SQLite thread-affinity crash.** Once the above was fixed, the first REST request through a
  store touched a SQLite connection from a different thread than the one that created it,
  raising `sqlite3.ProgrammingError`. Fixed by opening `SQLiteMemoryStore`'s and `LocalTracer`'s
  connections with `check_same_thread=False`.

Both bugs were caught while building an end-to-end Colab smoke test
(`genaiscope_v0.4.0_colab_test.ipynb`) against the real PyPI v0.4.0 release, and are confirmed
fixed by `tests/test_server_api.py` (now 7/7 passing).

No API changes. No action needed beyond upgrading.
