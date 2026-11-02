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
    Fallback for when a record carries no decodable mask.
    """
    polys: List[Polygon] = []
    for m in BOX_RE.finditer(sam_text or ""):
        x1 = float(m.group("x1"))
        y1 = float(m.group("y1"))
        x2 = float(m.group("x2"))
        y2 = float(m.group("y2"))
        polys.append([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
    return polys


_TOKEN_RE = re.compile(r"<\|(box|mask);(.*?)\|>", re.DOTALL)
_MASK_DATA_RE = re.compile(r"data=(\d+),(\d+),(.+)", re.DOTALL)


def _raster_to_polygon(raster: bytes, width: int, height: int, ox: float, oy: float):
    """Row-run rectangles -> one simplified polygon in image pixel space."""
    import numpy as np
    from shapely.geometry import box as shp_box
    from shapely.ops import unary_union

    arr = np.frombuffer(bytes(raster), dtype=np.uint8).reshape(height, width)
    rects = []
    for row in range(height):
        ones = np.flatnonzero(arr[row])
        if ones.size == 0:
            continue
        splits = np.where(np.diff(ones) > 1)[0]
        starts = np.concatenate(([0], splits + 1))
        ends = np.concatenate((splits, [ones.size - 1]))
        for s, e in zip(starts, ends):
            rects.append(
                shp_box(ox + int(ones[s]), oy + row, ox + int(ones[e]) + 1, oy + row + 1)
            )
    if not rects:
        return None
    union = unary_union(rects)
    if union.is_empty:
        return None
    if union.geom_type == "MultiPolygon":
        union = max(union.geoms, key=lambda g: g.area)
    union = union.simplify(1.5, preserve_topology=True)
    if union.is_empty or union.geom_type != "Polygon":
        return None
    return [(round(float(x), 1), round(float(y), 1)) for x, y in union.exterior.coords]


def masks_to_polygons(sam_text: str) -> List[Polygon]:
    """Masks decoded where possible; box rectangles otherwise."""
    return masks_to_polygons_with_meta(sam_text)[0]


def masks_to_polygons_with_meta(sam_text: str) -> tuple[List[Polygon], bool]:
    """
    Pair each SAM box with its following mask token, decode the mask
    (meta-sam-parser) and return the true outline in image pixel space.
    Records without a decodable mask fall back to their box rectangle.

    Returns (polygons, used_mask) — used_mask is True when at least one
    record decoded from a real mask, so layout can skip AABB overbox
    erosion designed for inflated rectangles.
    """
    try:
        from meta_sam_parser import SegmentationMask, decode_mask_to_raster
    except Exception:
        return boxes_to_polygons(sam_text), False

    polys: List[Polygon] = []
    used_mask = False
    pending_box: tuple[float, float, float, float] | None = None
    for kind, body in _TOKEN_RE.findall(sam_text or ""):
        if kind == "box":
            fields = dict(p.split("=", 1) for p in body.split(";") if "=" in p)
            try:
                pending_box = (
                    float(fields["x1"]),
                    float(fields["y1"]),
                    float(fields["x2"]),
                    float(fields["y2"]),
                )
            except (KeyError, ValueError):
                pending_box = None
            continue
        # mask token
        if pending_box is None:
            continue
        x1, y1, x2, y2 = pending_box
        pending_box = None
        m = _MASK_DATA_RE.search(body)
        poly = None
        if m:
            height, width, payload = int(m.group(1)), int(m.group(2)), m.group(3).strip()
            try:
                mask = SegmentationMask(
                    encoding="one_bit" if payload.startswith("!") else "lossless",
                    payload=payload,
                    width=width,
                    height=height,
                )
                poly = _raster_to_polygon(
                    decode_mask_to_raster(mask), width, height, x1, y1
                )
            except Exception:
                poly = None
        if poly:
            used_mask = True
        polys.append(poly if poly else [(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
    # Boxes that never got a mask still count (defensive; SAM pairs them).
    if not polys:
        return boxes_to_polygons(sam_text), False
    return polys, used_mask
