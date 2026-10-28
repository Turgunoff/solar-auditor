#!/usr/bin/env python3
"""End-to-end mock pipeline smoke test (no Meta API required)."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.api.endpoints import PRESETS, _run_pipeline  # noqa: E402
from app.core.config import get_settings  # noqa: E402


def main() -> int:
    settings = get_settings()
    settings.ensure_dirs()
    print("mode:", settings.mode_label())
    print("message:", settings.public_status()["message"])

    failures = 0
    for preset in PRESETS:
        src = settings.sample_data_dir / preset["filename"]
        if not src.exists():
            print("MISSING sample", src)
            failures += 1
            continue
        dest = settings.uploads_dir / f"smoke_{preset['id']}.jpg"
        shutil.copy2(src, dest)
        res = _run_pipeline(
            dest,
            f"/static/uploads/{dest.name}",
            preset["meters_per_pixel"],
            preset["id"],
        )
        ok = res.layout.total_panels > 0 and res.analytics.system_capacity_kw > 0
        print(
            f"{preset['id']}: panels={res.layout.total_panels} "
            f"kWp={res.analytics.system_capacity_kw} "
            f"seg={res.provider.segmentation} ok={ok}"
        )
        if not ok:
            failures += 1
            print(json.dumps(json.loads(res.model_dump_json()), indent=2)[:500])

    print("PASS" if failures == 0 else f"FAIL ({failures})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
