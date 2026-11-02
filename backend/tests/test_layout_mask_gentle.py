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
