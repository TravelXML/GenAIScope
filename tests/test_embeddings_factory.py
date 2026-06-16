"""Tests for the embedder factory — always runs."""

import pytest

from genaiscope.core.errors import EmbeddingBackendError
from genaiscope.embeddings.factory import get_embedder
from genaiscope.embeddings.local_hash import LocalHashEmbedder


def test_default_is_local_hash() -> None:
    emb = get_embedder()
    assert isinstance(emb, LocalHashEmbedder)


def test_explicit_local() -> None:
    emb = get_embedder("local")
    assert isinstance(emb, LocalHashEmbedder)


def test_local_hash_alias() -> None:
    emb = get_embedder("local_hash")
    assert isinstance(emb, LocalHashEmbedder)


def test_unknown_backend_raises() -> None:
    with pytest.raises(EmbeddingBackendError):
        get_embedder("nonexistent_backend")


def test_sentence_transformers_missing_raises() -> None:
    """Should raise EmbeddingBackendError if sentence-transformers not installed."""
    try:
        import sentence_transformers  # noqa: F401
        pytest.skip("sentence-transformers is installed — skip missing-dep test")
    except ImportError:
        with pytest.raises(EmbeddingBackendError, match="sentence-transformers"):
            get_embedder("sentence-transformers")


def test_openai_missing_key_raises() -> None:
    """Should raise EmbeddingBackendError when openai installed but no key set."""
    import os

    try:
        import openai  # noqa: F401
    except ImportError:
        pytest.skip("openai not installed")

    key_backup = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with pytest.raises(EmbeddingBackendError, match="OPENAI_API_KEY"):
            get_embedder("openai")
    finally:
        if key_backup:
            os.environ["OPENAI_API_KEY"] = key_backup
