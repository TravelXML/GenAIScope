"""Vector store abstraction for GenAIScope."""

from genaiscope.vector.base import BaseVectorStore
from genaiscope.vector.factory import get_vector_store
from genaiscope.vector.local_vector import LocalVectorStore
from genaiscope.vector.models import VectorMatch, VectorRecord

__all__ = [
    "BaseVectorStore",
    "LocalVectorStore",
    "VectorMatch",
    "VectorRecord",
    "get_vector_store",
]
