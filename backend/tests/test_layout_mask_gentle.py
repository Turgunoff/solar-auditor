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
