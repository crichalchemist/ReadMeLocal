from pathlib import Path

from backend.library import scan_library


def test_scan_library_filters_and_sorts(tmp_path: Path):
    (tmp_path / "A.pdf").write_text("x", encoding="utf-8")
    (tmp_path / "b.epub").write_text("x", encoding="utf-8")
    (tmp_path / "note.txt").write_text("x", encoding="utf-8")

    results = scan_library(tmp_path)
    names = [item["title"] for item in results]

    assert names == ["A", "b"]
    assert all(item["ext"] in (".pdf", ".epub") for item in results)
