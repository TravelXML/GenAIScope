"""Tests for local file memory."""

from genaiscope.files import FileMemory


def test_file_memory_adds_supported_files_and_searches(tmp_path):
    db_path = tmp_path / "memory.db"
    (tmp_path / "notes.txt").write_text(
        "Installation uses pip install genaiscope.", encoding="utf-8"
    )
    (tmp_path / "readme.md").write_text("# Install\nUse the dashboard.", encoding="utf-8")
    (tmp_path / "data.json").write_text('{"install": "pip"}', encoding="utf-8")
    (tmp_path / "bad.json").write_text("{bad", encoding="utf-8")
    (tmp_path / "data.csv").write_text("name,value\ninstall,pip\n", encoding="utf-8")

    files = FileMemory(db_path=db_path, chunk_size=80, chunk_overlap=10)
    for name in ["notes.txt", "readme.md", "data.json", "bad.json", "data.csv"]:
        assert files.add_file(tmp_path / name)

    assert files.search("installation")
    stats = files.stats()
    assert stats["total_files"] == 5
    assert stats["total_chunks"] >= 5
