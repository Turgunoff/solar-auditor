"""Mask outlines skip AABB overbox erosion but keep the pitched south cut."""

from app.core.config import Settings
from app.services.layout_engine import place_panels, usable_area_m2


def test_mask_outline_packs_more_than_aggressive():
    s = Settings(use_mock=True)
    roof = [[(0, 0), (300, 0), (300, 120), (0, 120)]]
    aggr = place_panels(roof, [], 300, 120, 0.05, s, sam_overbox=True, pitched=True)
    mask = place_panels(
        roof, [], 300, 120, 0.05, s, sam_overbox=True, pitched=True, mask_outlines=True
    )
    assert mask.total_panels > aggr.total_panels > 0
    assert usable_area_m2(
        roof, [], 0.05, s, width_px=300, height_px=120,
        sam_overbox=True, pitched=True, mask_outlines=True,
    ) > usable_area_m2(
        roof, [], 0.05, s, width_px=300, height_px=120,
        sam_overbox=True, pitched=True,
    )


def test_mask_flat_covers_full_roof():
    s = Settings(use_mock=True)
    roof = [[(0, 0), (300, 0), (300, 120), (0, 120)]]
    flat = place_panels(
        roof, [], 300, 120, 0.05, s, sam_overbox=True, pitched=False, mask_outlines=True
    )
    pitched = place_panels(
        roof, [], 300, 120, 0.05, s, sam_overbox=True, pitched=True, mask_outlines=True
    )
    assert flat.total_panels > pitched.total_panels


def test_mask_flat_uses_envelope_when_mask_is_partial():
    """Incomplete flat mask still packs the warehouse rectangle."""
    s = Settings(use_mock=True)
    # L-shaped mask missing the right strip of a 300×120 flat roof
    l_mask = [[(0, 0), (300, 0), (300, 60), (200, 60), (200, 120), (0, 120)]]
    partial_pack = place_panels(
        l_mask, [], 300, 120, 0.05, s,
        sam_overbox=True, pitched=False, mask_outlines=True,
    )
    full = place_panels(
        [[(0, 0), (300, 0), (300, 120), (0, 120)]], [], 300, 120, 0.05, s,
        sam_overbox=True, pitched=False, mask_outlines=True,
    )
    # Envelope fill should recover nearly full-rectangle density
    assert partial_pack.total_panels >= full.total_panels * 0.9


def test_mask_outlines_medium_obstacle_keepout():
    """Mask mode uses medium HVAC keepout — clears gear, keeps density."""
    from shapely.geometry import Point, box

    s = Settings(use_mock=True)
    mpp = 0.05
    roof = [[(0, 0), (400, 0), (400, 200), (0, 200)]]
    hvac = [[(160, 70), (240, 70), (240, 130), (160, 130)]]
    gentle = place_panels(
        roof, hvac, 400, 200, mpp, s,
        sam_overbox=True, pitched=False, mask_outlines=True,
    )
    free = place_panels(
        roof, [], 400, 200, mpp, s,
        sam_overbox=True, pitched=False, mask_outlines=True,
    )
    assert gentle.total_panels < free.total_panels
    setback_px = s.setback_m / mpp
    panel_w = s.panel_width_m / mpp
    medium = max(setback_px * 1.6, panel_w * 0.35)
    forbidden = box(160, 70, 240, 130).buffer(medium * 0.85)
    for p in gentle.panels:
        assert not forbidden.contains(Point(p.x, p.y)), p


def test_expand_flat_mask_includes_nearby_hvac_strip():
    from app.services.layout_engine import expand_flat_mask_roofs
    from shapely.geometry import Polygon

    s = Settings(use_mock=True)
    # Roof stops at x=300; HVAC sits on membrane at x=310–380
    roof = [[(0, 0), (300, 0), (300, 200), (0, 200)]]
    hvac = [[(310, 80), (380, 80), (380, 140), (310, 140)]]
    expanded = expand_flat_mask_roofs(roof, hvac, 0.05, s)
    poly = Polygon(expanded[0])
    assert poly.bounds[2] > 300  # grew past original right edge
    # Rim HVAC also pushes past the gear box toward the parapet
    panel_w = s.panel_width_m / 0.05
    assert poly.bounds[2] >= 380 + panel_w * 5
    # Packing on expanded roof should place more than the truncated mask alone
    trunc = place_panels(
        roof, hvac, 400, 200, 0.05, s,
        sam_overbox=True, pitched=False, mask_outlines=True,
    )
    full = place_panels(
        expanded, hvac, 400, 200, 0.05, s,
        sam_overbox=True, pitched=False, mask_outlines=True,
    )
    assert full.total_panels > trunc.total_panels


def test_expand_rim_pad_reaches_preset3_style_membrane():
    """Right-rim HVAC past the SAM mask must cover leftover white membrane."""
    from app.services.layout_engine import expand_flat_mask_roofs
    from shapely.geometry import Polygon

    s = Settings(use_mock=True)
    # Incomplete SAM stops mid-roof; HVAC sits further right on the membrane
    roof = [[(250, 210), (1200, 210), (1200, 875), (250, 875)]]
    hvac = [[(1228, 736), (1355, 736), (1355, 814), (1228, 814)]]
    # Interior HVAC on the left must not pull the left edge into parking
    interior = [[(400, 400), (500, 400), (500, 480), (400, 480)]]
    expanded = expand_flat_mask_roofs(roof, [hvac[0], interior[0]], 0.05, s)
    poly = Polygon(expanded[0])
    assert poly.bounds[2] >= 1355 + 150  # covers leftover membrane strip
    assert poly.bounds[0] >= 240  # left edge stays near original mask
