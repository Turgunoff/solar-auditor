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


def _pack_at(
    geom: Polygon,
    panel_w: float,
    panel_h: float,
    gap: float,
    angle: float,
    offset_x: float,
    offset_y: float,
) -> List[Panel]:
    """One grid phase: panels fully inside geom, centers in world pixels."""
    if geom.is_empty or geom.area <= 0:
        return []
    centroid = geom.centroid
    local = shp_rotate(geom, -angle, origin=centroid, use_radians=False)
    minx, miny, maxx, maxy = local.bounds
    step_x = panel_w + gap
    step_y = panel_h + gap
    panels: List[Panel] = []
    y = miny + offset_y
    while y + panel_h <= maxy + 1e-6:
        x = minx + offset_x
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
                        id=0,
                        x=round(float(world.x), 2),
                        y=round(float(world.y), 2),
                        width=round(panel_w, 2),
                        height=round(panel_h, 2),
                        rotation=round(angle % 180.0, 2),
                    )
                )
            x += step_x
        y += step_y
    return panels


def _pack_oriented(
    geom: Polygon,
    panel_w: float,
    panel_h: float,
    gap: float,
    start_id: int,
) -> Tuple[List[Panel], int]:
    """Pack panels; try roof-angle + axis-aligned, both orientations, 4 phases.

    A single grid origin leaves an empty strip when the leftover width/height
    is just under one module — commercial flat roofs showed this as a large
    white patch inside the green roof outline. Searching phases fills it.
    """
    if geom.is_empty or geom.area <= 0:
        return [], start_id

    roof_angle = _rect_angle_deg(geom)
    angles = []
    for a in (roof_angle, 0.0, 90.0):
        a = a % 180.0
        if not any(abs(a - b) < 0.5 or abs(a - b) > 179.5 for b in angles):
            angles.append(a)

    best: List[Panel] = []
    for w, h in ((panel_w, panel_h), (panel_h, panel_w)):
        step_x = w + gap
        step_y = h + gap
        for angle in angles:
            for ox in (0.0, step_x * 0.5):
                for oy in (0.0, step_y * 0.5):
                    packed = _pack_at(geom, w, h, gap, angle, ox, oy)
                    if len(packed) > len(best):
                        best = packed

    panels: List[Panel] = []
    panel_id = start_id
    for p in best:
        panels.append(
            Panel(
                id=panel_id,
                x=p.x,
                y=p.y,
                width=p.width,
                height=p.height,
                rotation=p.rotation,
            )
        )
        panel_id += 1
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


def _poly_to_points(poly: Polygon) -> List[Point]:
    if poly.is_empty:
        return []
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    coords = list(poly.exterior.coords)
    if len(coords) > 1 and coords[0] == coords[-1]:
        coords = coords[:-1]
    return [(float(x), float(y)) for x, y in coords]


def _extend_hull_past_rim_equipment(
    hull: Polygon,
    equipment: List[Polygon],
    original_roof: Polygon,
    panel_w: float,
    panel_h: float,
) -> Polygon:
    """Push hull edges outward when HVAC sits past the SAM mask rim.

    SAM + HVAC hull often stops at the equipment box while the white
    membrane continues several metres to the parapet (Preset 3 right strip).
    Only pad sides where gear protrudes past the original mask — interior
    HVAC on an already-correct edge must not grow into parking.
    """
    if hull.is_empty or not equipment or original_roof.is_empty:
        return hull
    minx, miny, maxx, maxy = hull.bounds
    o_minx, o_miny, o_maxx, o_maxy = original_roof.bounds
    rim_x = max(panel_w, 1.0)
    rim_y = max(panel_h, 1.0)
    # ~9 m of leftover membrane past rim gear at typical commercial scale.
    pad_x = panel_w * 5.5
    pad_y = panel_h * 5.5
    for obs in equipment:
        ox1, oy1, ox2, oy2 = obs.bounds
        # Require meaningful protrusion past the SAM mask (ignore noise).
        protrude = max(panel_w, panel_h) * 0.5
        if ox2 >= maxx - rim_x and ox2 > o_maxx + protrude:
            maxx = max(maxx, ox2 + pad_x)
        if ox1 <= minx + rim_x and ox1 < o_minx - protrude:
            minx = min(minx, ox1 - pad_x)
        if oy2 >= maxy - rim_y and oy2 > o_maxy + protrude:
            maxy = max(maxy, oy2 + pad_y)
        if oy1 <= miny + rim_y and oy1 < o_miny - protrude:
            miny = min(miny, oy1 - pad_y)
    grown = box(minx, miny, maxx, maxy)
    return grown if not grown.is_empty else hull


def _snap_hull_to_bright_membrane(
    hull: Polygon,
    image_path: str,
    panel_w: float,
    panel_h: float,
) -> Polygon:
    """Grow hull edges across leftover white membrane (no HVAC cue needed).

    Preset 3 SAM stopped ~167 px above the parapet while the membrane kept
    going — rim-HVAC pad could not help because gear sat inside the mask.
    Walk each edge outward while brightness stays roof-like; allow short
    dark gaps for HVAC, stop at asphalt/trees.
    """
    try:
        from PIL import Image
        import numpy as np
    except Exception:
        return hull
    try:
        arr = np.asarray(Image.open(image_path).convert("RGB"))
    except Exception:
        return hull
    if arr.ndim != 3 or arr.size == 0:
        return hull
    bri = arr.mean(axis=2)
    img_h, img_w = bri.shape
    minx, miny, maxx, maxy = hull.bounds
    # Interior reference brightness of the known roof patch
    ix0 = max(0, int(minx + (maxx - minx) * 0.2))
    ix1 = min(img_w, int(maxx - (maxx - minx) * 0.2))
    iy0 = max(0, int(miny + (maxy - miny) * 0.2))
    iy1 = min(img_h, int(maxy - (maxy - miny) * 0.2))
    if ix1 <= ix0 + 2 or iy1 <= iy0 + 2:
        return hull
    interior = bri[iy0:iy1, ix0:ix1]
    thr = float(max(150.0, np.median(interior) * 0.82))
    max_ext_x = panel_w * 8.0
    max_ext_y = panel_h * 12.0
    gap_tol = max(panel_h * 2.5, 40.0)

    def _bright_frac(x_samples: List[int], y: int) -> float:
        if y < 0 or y >= img_h or not x_samples:
            return 0.0
        vals = [bri[y, x] for x in x_samples if 0 <= x < img_w]
        if not vals:
            return 0.0
        return sum(1 for v in vals if v >= thr) / len(vals)

    def _walk(start: float, direction: int, limit: float, horizontal: bool) -> float:
        # direction: +1 outward toward increasing coord, -1 decreasing
        pos = start
        dark_run = 0.0
        last_bright = start
        xs = [
            int(minx + (maxx - minx) * t)
            for t in (0.15, 0.3, 0.5, 0.7, 0.85)
        ]
        ys = [
            int(miny + (maxy - miny) * t)
            for t in (0.15, 0.3, 0.5, 0.7, 0.85)
        ]
        step = max(2.0, min(panel_w, panel_h) * 0.25)
        traveled = 0.0
        while traveled < limit:
            pos += direction * step
            traveled += step
            if horizontal:
                # walking in x; sample along y
                if pos < 0 or pos >= img_w:
                    break
                frac = sum(
                    1 for y in ys if 0 <= y < img_h and bri[y, int(pos)] >= thr
                ) / max(len(ys), 1)
            else:
                if pos < 0 or pos >= img_h:
                    break
                frac = _bright_frac(xs, int(pos))
            if frac >= 0.55:
                dark_run = 0.0
                last_bright = pos
            else:
                dark_run += step
                if dark_run > gap_tol:
                    break
        return last_bright

    new_maxy = max(maxy, _walk(maxy, +1, max_ext_y, horizontal=False))
    new_miny = min(miny, _walk(miny, -1, max_ext_y, horizontal=False))
    new_maxx = max(maxx, _walk(maxx, +1, max_ext_x, horizontal=True))
    new_minx = min(minx, _walk(minx, -1, max_ext_x, horizontal=True))
    # Cap by walk limits (brightness already stops at asphalt/trees).
    w0, h0 = maxx - minx, maxy - miny
    new_minx = max(new_minx, minx - max(w0 * 0.25, max_ext_x))
    new_maxx = min(new_maxx, maxx + max(w0 * 0.25, max_ext_x))
    new_miny = max(new_miny, miny - max(h0 * 0.25, max_ext_y))
    new_maxy = min(new_maxy, maxy + max(h0 * 0.5, max_ext_y))
    grown = box(new_minx, new_miny, new_maxx, new_maxy)
    return grown if not grown.is_empty else hull


def expand_flat_mask_roofs(
    roof_polygons: List[List[Point]],
    obstacles: List[List[Point]],
    meters_per_pixel: float,
    settings: Settings,
    image_path: str | None = None,
) -> List[List[Point]]:
    """Grow incomplete flat SAM masks to the full white roof membrane.

    Live masks often stop mid-warehouse while HVAC or leftover membrane sit
    just outside the outline — Preset 3 left empty right/bottom strips.
    Hull with on-band obstacles, pad past rim HVAC, then snap remaining
    edges to bright membrane when an aerial path is available.
    """
    roofs = [_to_polygon(p) for p in roof_polygons]
    roofs = [r for r in roofs if r is not None]
    if not roofs:
        return roof_polygons
    panel_w = settings.panel_width_m / meters_per_pixel
    panel_h = settings.panel_height_m / meters_per_pixel
    expanded: List[Polygon] = []
    for roof in roofs:
        minx, miny, maxx, maxy = roof.bounds
        cands: List[Polygon] = [roof]
        equipment: List[Polygon] = []
        for pts in obstacles:
            obs = _to_polygon(pts)
            if obs is None or obs.area > roof.area * 0.12:
                continue
            ox1, oy1, ox2, oy2 = obs.bounds
            if oy1 < miny - panel_h * 2 or oy2 > maxy + panel_h * 2:
                continue
            if ox2 < minx - panel_w * 4 or ox1 > maxx + panel_w * 4:
                continue
            if roof.buffer(panel_w * 3).intersects(obs) or (
                miny <= float(obs.centroid.y) <= maxy
            ):
                cands.append(obs)
                equipment.append(obs)
        hull = unary_union(cands).minimum_rotated_rectangle
        if hull.is_empty:
            hull = roof
        else:
            hull = _extend_hull_past_rim_equipment(
                hull, equipment, roof, panel_w, panel_h
            )
        if image_path:
            hull = _snap_hull_to_bright_membrane(
                hull, image_path, panel_w, panel_h
            )
        expanded.append(hull)
    return [_poly_to_points(r) for r in expanded if _poly_to_points(r)]


def place_panels(
    roof_polygons: List[List[Point]],
    obstacles: List[List[Point]],
    width_px: int,
    height_px: int,
    meters_per_pixel: float,
    settings: Settings,
    sam_overbox: bool = True,
    pitched: bool = True,
    mask_outlines: bool = False,
) -> LayoutResult:
    """Pack panels onto roof polygons.

    sam_overbox=True applies the aggressive SAM-AABB handling (20% shrink,
    central-roof pick, south-half cut) for live SAM boxes that over-include
    yards and both gable faces. Pass False for tight outlines (mock
    templates) where that erosion would destroy small roofs.
    pitched=False skips the south-half cut for flat roofs, where every
    orientation is usable.
    mask_outlines=True means the polygons are decoded SAM mask outlines,
    not inflated AABBs — roof shrink uses plain setback (not 20% AABB
    erosion) while the south-half cut still applies for pitched roofs.
    Obstacle keepout: fat for AABB overbox mode; medium for true mask
    outlines (equipment clearance without the 988→500 panel density crash).
    """
    # True masks need only setback erosion, not AABB overbox handling.
    aggressive = sam_overbox and not mask_outlines
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

    # Trees / HVAC keep-out: fat for inflated AABB mode; medium for true masks.
    blocked = None
    if obstacle_polys:
        if aggressive:
            keepout = max(setback_px * 2.5, panel_w * 0.6)
        elif sam_overbox:
            keepout = max(setback_px * 1.6, panel_w * 0.35)
        else:
            keepout = setback_px
        blocked = unary_union(obstacle_polys).buffer(keepout)

    panels: List[Panel] = []
    panel_id = 1

    for roof in roofs:
        if aggressive:
            usable = _shrink_sam_overbox(roof, meters_per_pixel, setback_px)
        elif mask_outlines and not pitched:
            # Flat commercial: pack oriented envelope of (possibly expanded) mask.
            env = roof.minimum_rotated_rectangle
            usable = env.buffer(-setback_px) if setback_px > 0 else env
            if usable.is_empty:
                usable = env
        else:
            usable = roof.buffer(-setback_px) if setback_px > 0 else roof
            if usable.is_empty:
                usable = roof
        if blocked is not None and not usable.is_empty:
            usable = usable.difference(blocked)
        if sam_overbox and pitched:
            usable = sun_facing_region(usable, meters_per_pixel)
        if usable.is_empty:
            continue
        geoms = list(usable.geoms) if usable.geom_type == "MultiPolygon" else [usable]
        for geom in geoms:
            if geom.area < min_area * 0.25:
                continue
            packed, panel_id = _pack_oriented(geom, panel_w, panel_h, gap, panel_id)
            panels.extend(packed)

    if not panels and (sam_overbox or pitched):
        # SAM heuristics (20% shrink + south cut) can erase a small/flat
        # roof entirely. Retry once with plain setback packing so a real
        # roof never reports 0 panels while a usable area exists.
        retry = place_panels(
            roof_polygons,
            obstacles,
            width_px,
            height_px,
            meters_per_pixel,
            settings,
            sam_overbox=False,
            pitched=False,
        )
        if retry.total_panels:
            return retry

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
    pitched: bool = True,
    mask_outlines: bool = False,
) -> float:
    roofs = [_to_polygon(p) for p in roof_polygons]
    roofs = [r for r in roofs if r is not None]
    if not roofs:
        return 0.0
    w = width_px or int(max(max(p[0] for p in pts) for pts in roof_polygons) + 1)
    h = height_px or int(max(max(p[1] for p in pts) for pts in roof_polygons) + 1)
    setback_px = settings.setback_m / meters_per_pixel
    aggressive = sam_overbox and not mask_outlines
    if sam_overbox:
        roofs = _prefer_central_roofs(roofs, w, h, max_roofs=1)
        if aggressive:
            roofs = [_shrink_sam_overbox(r, meters_per_pixel, setback_px) for r in roofs]
        if pitched:
            roofs = [sun_facing_region(r, meters_per_pixel) for r in roofs]
    if mask_outlines and not pitched:
        roofs = [r.minimum_rotated_rectangle for r in roofs]
    if not aggressive:
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
    if aggressive:
        keepout = max(setback_px * 2.5, panel_w * 0.6)
    elif sam_overbox:
        keepout = max(setback_px * 1.6, panel_w * 0.35)
    else:
        keepout = setback_px
    if obs:
        usable = roof_union.difference(unary_union(obs).buffer(keepout))
    else:
        usable = roof_union
    return float(max(usable.area, 0.0) * (meters_per_pixel**2))
