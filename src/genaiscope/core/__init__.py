"""Core package initialization."""

from typing import Any


def __getattr__(name: str) -> Any:
    # Lazy by design: genaiscope.core is imported very early (it's the first
    # thing genaiscope/__init__.py touches), and GenAIScope itself pulls in
    # memory/tracing/doctor. Importing it eagerly here would risk a circular
    # import during that early bootstrap. PEP 562 module __getattr__ defers
    # the real import until something actually accesses GenAIScope.
    if name == "GenAIScope":
        from genaiscope.core.scope import GenAIScope

        return GenAIScope
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
