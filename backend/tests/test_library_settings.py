from pathlib import Path

from fastapi.testclient import TestClient

import backend.main as main


def test_update_library_path_persists(tmp_path: Path):
    settings_path = tmp_path / "settings.yaml"
    settings_path.write_text("library_path: \"\"\n", encoding="utf-8")
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "Sample.pdf").write_text("x", encoding="utf-8")

    main.CONFIG_PATH = settings_path
    main.SETTINGS["library_path"] = ""

    client = TestClient(main.app)
    res = client.put("/api/library/path", json={"path": str(library_dir)})

    assert res.status_code == 200
    payload = res.json()
    assert payload["library_path"] == str(library_dir)
    assert payload["items"][0]["title"] == "Sample"
    assert f'library_path: "{library_dir}"' in settings_path.read_text(encoding="utf-8")
