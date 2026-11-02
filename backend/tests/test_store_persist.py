"""Project store survives restarts via disk persistence."""

from app.store import ProjectStore


def test_store_persists_to_disk(tmp_path):
    payload = {"project_id": "solar_proj_test1", "analytics": {"system_capacity_kw": 4.0}}
    ProjectStore(persist_dir=tmp_path).put("solar_proj_test1", payload)
    # Fresh instance (simulated restart) still finds the project.
    assert ProjectStore(persist_dir=tmp_path).get("solar_proj_test1") == payload


def test_store_missing_returns_none(tmp_path):
    assert ProjectStore(persist_dir=tmp_path).get("solar_proj_nope") is None
