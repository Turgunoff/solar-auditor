from __future__ import annotations

import re
from typing import List, Tuple

Point = Tuple[float, float]
Polygon = List[Point]

BOX_RE = re.compile(
    r"<\|box;x1=(?P<x1>\d+);y1=(?P<y1>\d+);x2=(?P<x2>\d+);y2=(?P<y2>\d+);w=(?P<w>\d+);h=(?P<h>\d+)(?:;c=[^|]+)?\|>"
)


def extract_output_text(response: dict) -> str:
    """Pull SAM wire text from a Responses API JSON body."""
    chunks: List[str] = []
    for item in response.get("output") or []:
        if item.get("type") != "message":
            continue
        for part in item.get("content") or []:
            if part.get("type") == "output_text" and part.get("text"):
                chunks.append(str(part["text"]))
    return "\n".join(chunks).strip()


def boxes_to_polygons(sam_text: str) -> List[Polygon]:
    """
    Convert SAM box tokens into axis-aligned polygons (pixel space).
    Mask decoding is optional later; boxes are enough for layout packing.
    """
    polys: List[Polygon] = []
    for m in BOX_RE.finditer(sam_text or ""):
        x1 = float(m.group("x1"))
        y1 = float(m.group("y1"))
        x2 = float(m.group("x2"))
        y2 = float(m.group("y2"))
        polys.append([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
    return polys
