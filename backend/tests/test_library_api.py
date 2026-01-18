from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


def test_library_endpoint_returns_books(tmp_path: Path, monkeypatch):
    (tmp_path / "Sample.pdf").write_text("Hello world.", encoding="utf-8")
    monkeypatch.setenv("README_LIBRARY_PATH", str(tmp_path))

    client = TestClient(app)
    res = client.get("/api/library")

    assert res.status_code == 200
    data = res.json()
    assert data[0]["title"] == "Sample"
