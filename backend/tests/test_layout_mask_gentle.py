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


def test_mask_outlines_keep_fat_obstacle_keepout():
    """Gentle roof shrink must not weaken HVAC/tree keepout (regression 2026-11-02)."""
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
    fat = max(setback_px * 2.5, panel_w * 0.6)
    # Centroids must stay outside ~90% of the fat keepout (not mere setback).
    forbidden = box(160, 70, 240, 130).buffer(fat * 0.9)
    for p in gentle.panels:
        assert not forbidden.contains(Point(p.x, p.y)), p
