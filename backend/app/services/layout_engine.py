from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from shapely.affinity import rotate as shp_rotate
from shapely.geometry import Point as ShpPoint
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from app.api.schemas import LayoutResult, Panel, PanelDimensions
from app.core.config import Settings

Point = Tuple[float, float]

# Above this → treat as flat commercial warehouse (pack full AABB).
# Below → pitched / campus roofs: SAM boxes over-include courtyards & both
# gable faces, so shrink + keep south half only (north-up aerial, +Y = south).
COMMERCIAL_FLAT_M2 = 2200.0
# Inward shrink of SAM AABB for non-commercial (fraction of shorter side).
SAM_BOX_SHRINK = 0.20


def _to_polygon(points: Sequence[Point]) -> Polygon | None:
    if len(points) < 3:
        return None
    poly = Polygon(points)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty or poly.area <= 0:
        return None
    return poly


def _rect_angle_deg(geom: Polygon) -> float:
    """Long-edge angle of the minimum rotated rectangle (degrees, CCW)."""
    rect = geom.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)
    if len(coords) < 3:
        return 0.0
    best = (0.0, 0.0)  # (length, angle)
    for i in range(4):
        x0, y0 = coords[i]
        x1, y1 = coords[i + 1]
        length = math.hypot(x1 - x0, y1 - y0)
        angle = math.degrees(math.atan2(y1 - y0, x1 - x0))
        if length > best[0]:
            best = (length, angle)
    return best[1]


def sun_facing_region(geom: Polygon, meters_per_pixel: float) -> Polygon:
    """For pitched / campus footprints, keep the south half only.

    Google / Map aerials are north-up. Image Y grows southward, so the
    sunnier gable face (northern hemisphere) is the half with larger Y.
    Large flat commercial roofs keep the full polygon.
    """
    if geom.is_empty or geom.area <= 0:
        return geom
    area_m2 = float(geom.area) * (meters_per_pixel**2)
    if area_m2 >= COMMERCIAL_FLAT_M2:
        return geom

    minx, miny, maxx, maxy = geom.bounds
    cy = float(geom.centroid.y)
    south_clip = box(minx - 2.0, cy, maxx + 2.0, maxy + 2.0)
    south = geom.intersection(south_clip)
    if south.is_empty or south.area < geom.area * 0.22:
        return geom
    if south.geom_type == "GeometryCollection":
        parts = [g for g in south.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        if not parts:
            return geom
        south = unary_union(parts)
    return south


def _shrink_sam_overbox(geom: Polygon, meters_per_pixel: float, setback_px: float) -> Polygon:
    """SAM returns AABBs that swallow courtyards — pull edges in for pitched sites."""
    if geom.is_empty:
        return geom
    area_m2 = float(geom.area) * (meters_per_pixel**2)
    minx, miny, maxx, maxy = geom.bounds
    short = min(maxx - minx, maxy - miny)
    if area_m2 >= COMMERCIAL_FLAT_M2:
        pad = setback_px
    else:
        pad = max(setback_px, short * SAM_BOX_SHRINK)
    shrunk = geom.buffer(-pad)
    return shrunk if not shrunk.is_empty else geom


def _pack_oriented(
    geom: Polygon,
    panel_w: float,
    panel_h: float,
    gap: float,
    start_id: int,
) -> Tuple[List[Panel], int]:
    """Pack panels aligned to geom's dominant roof orientation.

    Panel.x / Panel.y are the panel center in image pixel space.
    Panel.rotation is degrees CCW.
    """
    if geom.is_empty or geom.area <= 0:
        return [], start_id

    angle = _rect_angle_deg(geom)
    centroid = geom.centroid
    local = shp_rotate(geom, -angle, origin=centroid, use_radians=False)
    minx, miny, maxx, maxy = local.bounds
    step_x = panel_w + gap
    step_y = panel_h + gap

    panels: List[Panel] = []
    panel_id = start_id
    y = miny
    while y + panel_h <= maxy + 1e-6:
        x = minx
        while x + panel_w <= maxx + 1e-6:
            candidate = box(x, y, x + panel_w, y + panel_h)
            if local.contains(candidate):
                cx = x + panel_w / 2.0
                cy = y + panel_h / 2.0
                world = shp_rotate(
                    ShpPoint(cx, cy), angle, origin=centroid, use_radians=False
                )
                panels.append(
                    Panel(
                        id=panel_id,
                        x=round(float(world.x), 2),
                        y=round(float(world.y), 2),
                        width=round(panel_w, 2),
                        height=round(panel_h, 2),
                        rotation=round(angle % 180.0, 2),
                    )
                )
                panel_id += 1
            x += step_x
        y += step_y

    return panels, panel_id


def _prefer_central_roofs(
    roofs: List[Polygon],
    width_px: int,
    height_px: int,
    max_roofs: int = 2,
) -> List[Polygon]:
    """Keep the largest roof planes near the image center (drop yard/tree FPs)."""
    if len(roofs) <= max_roofs:
        return roofs
    cx, cy = width_px / 2.0, height_px / 2.0
    diag = math.hypot(width_px, height_px) or 1.0
    scored: List[Tuple[float, Polygon]] = []
    for roof in roofs:
        rcx, rcy = float(roof.centroid.x), float(roof.centroid.y)
        dist = math.hypot(rcx - cx, rcy - cy) / diag
        # Area dominates; centrality breaks ties / kills edge sheds
        score = float(roof.area) * ((1.0 - min(dist, 1.0)) ** 1.5)
        scored.append((score, roof))
    scored.sort(key=lambda t: t[0], reverse=True)
    best = scored[0][0] or 1.0
    kept: List[Polygon] = []
    for score, roof in scored:
        if len(kept) >= max_roofs:
            break
        if score < best * 0.18:
            break
        kept.append(roof)
    return kept or [scored[0][1]]


def place_panels(
    roof_polygons: List[List[Point]],
    obstacles: List[List[Point]],
    width_px: int,
    height_px: int,
    meters_per_pixel: float,
    settings: Settings,
    sam_overbox: bool = True,
) -> LayoutResult:
    """Pack panels onto roof polygons.

    sam_overbox=True applies the aggressive SAM-AABB handling (20% shrink,
    central-roof pick, south-half cut) for live SAM boxes that over-include
    yards and both gable faces. Pass False for tight outlines (mock
    templates) where that erosion would destroy small roofs.
    """
    panel_w = settings.panel_width_m / meters_per_pixel
    panel_h = settings.panel_height_m / meters_per_pixel
    setback_px = settings.setback_m / meters_per_pixel
    gap = max(1.5, min(panel_w, panel_h) * 0.05)

    roofs = []
    for pts in roof_polygons:
        poly = _to_polygon(pts)
        if poly is not None:
            roofs.append(poly)
    if not roofs:
        return LayoutResult(
            total_panels=0,
            panel_dimensions=PanelDimensions(width=panel_w, height=panel_h),
            panels=[],
        )

    frame_area = max(float(width_px * height_px), 1.0)
    # ~12 m² minimum at known scale, or 0.6% of frame
    min_area = max(frame_area * 0.006, (12.0 / max(meters_per_pixel, 1e-6)) ** 2 * 0.12)
    roofs = [r for r in roofs if r.area >= min_area]
    if sam_overbox:
        # One primary roof — multi-box campus picks often tag courtyards as roof #2
        roofs = _prefer_central_roofs(roofs, width_px, height_px, max_roofs=1)
    if not roofs:
        return LayoutResult(
            total_panels=0,
            panel_dimensions=PanelDimensions(width=panel_w, height=panel_h),
            panels=[],
        )

    obstacle_polys = []
    for pts in obstacles:
        poly = _to_polygon(pts)
        if poly is None:
            continue
        if poly.area > frame_area * 0.35:
            continue
        obstacle_polys.append(poly)

    # Trees / courtyards need a fat keep-out so AABB packing doesn't fill yards
    blocked = None
    if obstacle_polys:
        keepout = (
            max(setback_px * 2.5, panel_w * 0.6) if sam_overbox else setback_px
        )
        blocked = unary_union(obstacle_polys).buffer(keepout)

    panels: List[Panel] = []
    panel_id = 1

    for roof in roofs:
        if sam_overbox:
            usable = _shrink_sam_overbox(roof, meters_per_pixel, setback_px)
        else:
            usable = roof.buffer(-setback_px) if setback_px > 0 else roof
            if usable.is_empty:
                usable = roof
        if blocked is not None and not usable.is_empty:
            usable = usable.difference(blocked)
        if sam_overbox:
            usable = sun_facing_region(usable, meters_per_pixel)
        if usable.is_empty:
            continue
        geoms = list(usable.geoms) if usable.geom_type == "MultiPolygon" else [usable]
        for geom in geoms:
            if geom.area < min_area * 0.25:
                continue
            packed, panel_id = _pack_oriented(geom, panel_w, panel_h, gap, panel_id)
            panels.extend(packed)

    return LayoutResult(
        total_panels=len(panels),
        panel_dimensions=PanelDimensions(
            width=round(panel_w, 2),
            height=round(panel_h, 2),
        ),
        panels=panels,
    )


def usable_area_m2(
    roof_polygons: List[List[Point]],
    obstacles: List[List[Point]],
    meters_per_pixel: float,
    settings: Settings,
    width_px: int | None = None,
    height_px: int | None = None,
    sam_overbox: bool = True,
) -> float:
    roofs = [_to_polygon(p) for p in roof_polygons]
    roofs = [r for r in roofs if r is not None]
    if not roofs:
        return 0.0
    w = width_px or int(max(max(p[0] for p in pts) for pts in roof_polygons) + 1)
    h = height_px or int(max(max(p[1] for p in pts) for pts in roof_polygons) + 1)
    setback_px = settings.setback_m / meters_per_pixel
    if sam_overbox:
        roofs = _prefer_central_roofs(roofs, w, h, max_roofs=1)
        roofs = [_shrink_sam_overbox(r, meters_per_pixel, setback_px) for r in roofs]
        roofs = [sun_facing_region(r, meters_per_pixel) for r in roofs]
    else:
        shrunk = [
            r.buffer(-setback_px) if setback_px > 0 else r for r in roofs
        ]
        roofs = [s if not s.is_empty else r for s, r in zip(shrunk, roofs)]
    roofs = [r for r in roofs if r is not None and not r.is_empty]
    if not roofs:
        return 0.0
    roof_union = unary_union(roofs)
    obs = [_to_polygon(p) for p in obstacles]
    obs = [o for o in obs if o is not None and o.area < roof_union.area * 0.85]
    panel_w = settings.panel_width_m / meters_per_pixel
    keepout = max(setback_px * 2.5, panel_w * 0.6) if sam_overbox else setback_px
    if obs:
        usable = roof_union.difference(unary_union(obs).buffer(keepout))
    else:
        usable = roof_union
    return float(max(usable.area, 0.0) * (meters_per_pixel**2))
