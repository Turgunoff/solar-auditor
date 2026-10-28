"""Upload guards + static retention cleanup."""

import os
import time

from app.core.config import Settings
from app.services.cleanup import cleanup_old_files


class _StubSettings:
    """Minimal stand-in: cleanup_old_files only needs the three dirs + days."""
    def __init__(self, root, days=7):
        self._root = root
        self.static_retention_days = days

    @property
    def uploads_dir(self):
        return self._root / "uploads"

    @property
    def renders_dir(self):
        return self._root / "renders"

    @property
    def exports_dir(self):
        return self._root / "exports"


def test_cleanup_removes_only_stale_files(tmp_path):
    for d in ("uploads", "renders", "exports"):
        (tmp_path / d).mkdir()
    old = tmp_path / "uploads" / "old.jpg"
    new = tmp_path / "renders" / "new.jpg"
    keep = tmp_path / "renders" / ".gitkeep"
    old.write_bytes(b"x")
    new.write_bytes(b"y")
    keep.write_bytes(b"")
    ancient = time.time() - 8 * 86400
    os.utime(old, (ancient, ancient))

    stats = cleanup_old_files(_StubSettings(tmp_path))
    assert stats == {"removed": 1, "kept": 1}
    assert not old.exists()
    assert new.exists()
    assert keep.exists()


def test_cleanup_missing_dirs_ok(tmp_path):
    stats = cleanup_old_files(_StubSettings(tmp_path))
    assert stats == {"removed": 0, "kept": 0}


def test_upload_guard_defaults():
    s = Settings(use_mock=True)
    assert s.max_upload_mb == 15
    assert s.min_upload_px == 64
    assert s.max_upload_mp == 50.0
    assert s.static_retention_days == 7
