"""Pluggable embedding providers for GenAIScope."""

from genaiscope.embeddings.base import BaseEmbedder
from genaiscope.embeddings.factory import get_embedder
from genaiscope.embeddings.local_hash import LocalHashEmbedder
from genaiscope.embeddings.models import EmbeddingResult

__all__ = [
    "BaseEmbedder",
    "EmbeddingResult",
    "LocalHashEmbedder",
    "get_embedder",
]
