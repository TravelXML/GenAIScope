"""Namespace helpers shared by production backends."""

from __future__ import annotations


def normalize_namespace(namespace: str | None) -> str:
    """Return a stable backend namespace."""

    clean = (namespace or "genaiscope").strip().replace(" ", "_")
    return clean or "genaiscope"
