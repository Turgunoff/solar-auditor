from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

_DEFAULT_DIR = Path(__file__).resolve().parents[1] / "static" / "exports"


class ProjectStore:
    """In-memory project store with disk persistence (survives restarts)."""

    def __init__(self, persist_dir: Path | None = None) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}
        self._dir = Path(persist_dir) if persist_dir is not None else _DEFAULT_DIR

    def _path(self, project_id: str) -> Path:
        safe = "".join(c for c in project_id if c.isalnum() or c in "_-")
        return self._dir / f"{safe}.json"

    def put(self, project_id: str, payload: Dict[str, Any]) -> None:
        self._items[project_id] = payload
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._path(project_id).write_text(
                json.dumps(payload), encoding="utf-8"
            )
        except OSError:
            pass  # Memory copy still serves this process.

    def get(self, project_id: str) -> Optional[Dict[str, Any]]:
        if project_id in self._items:
            return self._items[project_id]
        try:
            path = self._path(project_id)
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._items[project_id] = data
                    return data
        except (OSError, ValueError):
            pass
        return None


store = ProjectStore()
