"""Every key in .env.example must map to a Settings field (no silent drift)."""

from pathlib import Path

from app.core.config import BACKEND_ROOT, Settings

# Frontend-only keys, not backend settings.
IGNORED = {"VITE_GOOGLE_MAPS_API_KEY"}


def _example_keys():
    keys = set()
    for line in (BACKEND_ROOT.parent / ".env.example").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.add(line.split("=", 1)[0].strip())
    return keys - IGNORED


def test_env_example_matches_settings():
    fields = set(Settings.model_fields)
    missing = sorted(k.lower() for k in _example_keys() if k.lower() not in fields)
    assert not missing, f".env.example keys without Settings fields: {missing}"
