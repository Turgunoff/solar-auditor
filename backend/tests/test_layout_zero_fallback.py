"""A roof must not yield 0 panels only because SAM heuristics erased it."""

from app.core.config import Settings
from app.services.layout_engine import place_panels


def test_small_roof_still_gets_panels():
    # 140x50 px at 0.05 m/px = 7x2.5 m roof. SAM overbox shrink +
    # south-half cut leaves <1 panel height; the gentler retry must pack.
    s = Settings(use_mock=True)
    roof = [[(0, 0), (140, 0), (140, 50), (0, 50)]]
    res = place_panels(roof, [], 140, 50, 0.05, s, sam_overbox=True, pitched=True)
    assert res.total_panels >= 1


def test_empty_roof_stays_zero():
    s = Settings(use_mock=True)
    res = place_panels([], [], 140, 50, 0.05, s, sam_overbox=True, pitched=True)
    assert res.total_panels == 0
