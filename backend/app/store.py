from __future__ import annotations

from typing import Any, Dict, Optional


class ProjectStore:
    """Simple in-memory project store for the MVP."""

    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}

    def put(self, project_id: str, payload: Dict[str, Any]) -> None:
        self._items[project_id] = payload

    def get(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self._items.get(project_id)


store = ProjectStore()
