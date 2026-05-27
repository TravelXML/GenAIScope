"""Text chunking for file memory."""

from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks."""

    clean = text.strip()
    if not clean:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    overlap = max(0, min(chunk_overlap, chunk_size - 1))
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        chunk = clean[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        next_start = start + chunk_size - overlap
        if next_start <= start:
            break
        start = next_start
    return chunks
