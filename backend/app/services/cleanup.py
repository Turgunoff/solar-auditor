from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Never delete these, regardless of age.
KEEP_NAMES = {".gitkeep"}


def cleanup_old_files(settings: Settings, max_age_days: int | None = None) -> Dict[str, int]:
    """Delete stale generated files from uploads/renders/exports.

    Only regular files older than `max_age_days` are removed; directories,
    sample data, and KEEP_NAMES are never touched. Best-effort: per-file
    errors are logged and skipped. Returns {"removed": n, "kept": m}.
    """
    limit_days = max_age_days if max_age_days is not None else settings.static_retention_days
    cutoff = time.time() - limit_days * 86400
    removed, kept = 0, 0
    for directory in (settings.uploads_dir, settings.renders_dir, settings.exports_dir):
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if not path.is_file() or path.name in KEEP_NAMES:
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
                else:
                    kept += 1
            except OSError as exc:
                logger.warning("cleanup: skipping %s: %s", path, exc)
                kept += 1
    return {"removed": removed, "kept": kept}


def static_usage(settings: Settings) -> Dict[str, int]:
    """Count files and bytes per generated dir (for status/debugging)."""
    usage: Dict[str, int] = {}
    for name, directory in (
        ("uploads", settings.uploads_dir),
        ("renders", settings.renders_dir),
        ("exports", settings.exports_dir),
    ):
        files = [p for p in directory.iterdir()] if directory.is_dir() else []
        blobs = [p for p in files if p.is_file()]
        usage[f"{name}_files"] = len(blobs)
        usage[f"{name}_bytes"] = sum(p.stat().st_size for p in blobs if p.exists())
    return usage
