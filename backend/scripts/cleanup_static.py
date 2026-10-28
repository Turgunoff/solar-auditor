#!/usr/bin/env python3
"""Delete stale uploads/renders/exports older than retention (default 7 days).

Usage: ../.venv/bin/python scripts/cleanup_static.py [--days N]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.cleanup import cleanup_old_files, static_usage  # noqa: E402


def main() -> int:
    days = None
    args = sys.argv[1:]
    if "--days" in args:
        days = int(args[args.index("--days") + 1])
    settings = get_settings()
    settings.ensure_dirs()
    print("before:", static_usage(settings))
    stats = cleanup_old_files(settings, max_age_days=days)
    print("cleaned:", stats)
    print("after:", static_usage(settings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
