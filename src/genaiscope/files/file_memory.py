"""Local file memory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from genaiscope.files.chunking import chunk_text
from genaiscope.files.loaders import SUPPORTED_EXTENSIONS, load_file
from genaiscope.memory import MemoryItem, MemorySearchResult, MemoryStore
from genaiscope.memory.utils import iso_now


class FileMemory:
    """Index local TXT, MD, JSON, and CSV files into MemoryStore."""

    def __init__(
        self,
        memory_store: MemoryStore | None = None,
        db_path: str | Path | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ):
        self.memory_store = memory_store or MemoryStore(db_path=db_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def add_file(
        self,
        path: str | Path,
        tags: list[str] | None = None,
        user_id: str | None = None,
    ) -> list[MemoryItem]:
        """Add one supported file to memory."""

        file_path = Path(path)
        text, loader_meta = load_file(file_path)
        chunks = chunk_text(text, self.chunk_size, self.chunk_overlap)
        items: list[MemoryItem] = []
        total = len(chunks)
        for index, chunk in enumerate(chunks):
            metadata: dict[str, Any] = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix.lower(),
                "file_size": file_path.stat().st_size,
                "chunk_index": index,
                "total_chunks": total,
                "indexed_at": iso_now(),
                **loader_meta,
            }
            items.append(
                self.memory_store.add(
                    chunk,
                    memory_type="document",
                    user_id=user_id,
                    source="file",
                    tags=tags,
                    metadata=metadata,
                )
            )
        return items

    def add_folder(
        self,
        path: str | Path,
        recursive: bool = False,
        tags: list[str] | None = None,
        user_id: str | None = None,
    ) -> list[MemoryItem]:
        """Add supported files from a folder."""

        folder = Path(path)
        pattern = "**/*" if recursive else "*"
        items: list[MemoryItem] = []
        for file_path in sorted(folder.glob(pattern)):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                items.extend(self.add_file(file_path, tags=tags, user_id=user_id))
        return items

    def search(
        self,
        query: str,
        limit: int = 10,
        user_id: str | None = None,
    ) -> list[MemorySearchResult]:
        """Search indexed file chunks."""

        return self.memory_store.search(
            query,
            user_id=user_id,
            memory_type="document",
            limit=limit,
            mode="hybrid",
        )

    def list_files(self) -> list[dict[str, Any]]:
        """Return indexed file summaries."""

        files: dict[str, dict[str, Any]] = {}
        for item in self.memory_store.list(memory_type="document", limit=1000):
            file_path = item.metadata.get("file_path")
            if not file_path:
                continue
            current = files.setdefault(
                file_path,
                {
                    "file_path": file_path,
                    "file_name": item.metadata.get("file_name"),
                    "file_type": item.metadata.get("file_type"),
                    "file_size": item.metadata.get("file_size"),
                    "total_chunks": 0,
                    "indexed_at": item.metadata.get("indexed_at"),
                },
            )
            current["total_chunks"] += 1
        return list(files.values())

    def stats(self) -> dict[str, Any]:
        """Return file memory statistics."""

        files = self.list_files()
        by_type: dict[str, int] = {}
        total_chunks = 0
        for file in files:
            file_type = str(file.get("file_type") or "unknown")
            by_type[file_type] = by_type.get(file_type, 0) + 1
            total_chunks += int(file.get("total_chunks") or 0)
        return {
            "total_files": len(files),
            "total_chunks": total_chunks,
            "file_types": by_type,
            "recent_files": files[:10],
        }
