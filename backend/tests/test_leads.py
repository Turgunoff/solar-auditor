"""POST /api/leads stores server-side; bad email rejected."""

import json

import pytest
from fastapi import HTTPException

import app.api.endpoints as endpoints
from app.api.schemas import LeadIn


class _StubSettings:
    def __init__(self, root):
        self._root = root

    @property
    def exports_dir(self):
        return self._root

    def ensure_dirs(self):
        self._root.mkdir(parents=True, exist_ok=True)


def test_submit_lead_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(endpoints, "get_settings", lambda: _StubSettings(tmp_path))
    out = endpoints.submit_lead(
        LeadIn(name="A", email="a@b.co", company="C", message="hi")
    )
    assert out.stored == "server"
    lines = (tmp_path / "leads.jsonl").read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["email"] == "a@b.co" and "at" in record


def test_submit_lead_rejects_bad_email(tmp_path, monkeypatch):
    monkeypatch.setattr(endpoints, "get_settings", lambda: _StubSettings(tmp_path))
    with pytest.raises(HTTPException) as exc:
        endpoints.submit_lead(LeadIn(name="A", email="not-an-email", message="hi"))
    assert exc.value.status_code == 400
    assert not (tmp_path / "leads.jsonl").exists()
