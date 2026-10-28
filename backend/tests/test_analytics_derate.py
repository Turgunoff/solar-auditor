"""Analytics derate math + layout constant boundaries."""

from shapely.geometry import box

from app.core.config import Settings
from app.services.analytics import compute_analytics
from app.services.layout_engine import (
    COMMERCIAL_FLAT_M2,
    _shrink_sam_overbox,
    sun_facing_region,
)


def test_derate_reduces_generation():
    s = Settings(use_mock=True)
    assert s.derate == 0.85
    res = compute_analytics(10, 50.0, s)
    assert res.system_capacity_kw == 4.0
    assert res.annual_generation_kwh == round(4.0 * 1450.0 * 0.85, 1)
    # Savings follow derated generation
    assert res.annual_savings_usd == round(res.annual_generation_kwh * 0.12, 2)


def test_derate_one_restores_ideal():
    s = Settings(use_mock=True, derate=1.0)
    res = compute_analytics(10, 50.0, s)
    assert res.annual_generation_kwh == round(4.0 * 1450.0, 1)


def test_zero_panels_gives_none_roi():
    s = Settings(use_mock=True)
    res = compute_analytics(0, 0.0, s)
    assert res.system_capacity_kw == 0.0
    assert res.roi_years is None


def test_commercial_threshold_boundary():
    # Just below -> pitched handling (south half); just above -> full polygon.
    side_below = (COMMERCIAL_FLAT_M2 - 1.0) ** 0.5
    small = box(0, 0, side_below, side_below)
    south = sun_facing_region(small, 1.0)
    assert south.area < small.area
    side_above = (COMMERCIAL_FLAT_M2 + 1.0) ** 0.5
    big = box(0, 0, side_above, side_above)
    assert sun_facing_region(big, 1.0).area == big.area


def test_shrink_pad_branches():
    # Small roof: 20% of short side dominates setback.
    small = box(0, 0, 100, 100)
    shrunk = _shrink_sam_overbox(small, 0.1, 5.0)  # 100 m²
    assert [round(v, 6) for v in shrunk.bounds] == [20.0, 20.0, 80.0, 80.0]
    # Commercial roof: plain setback.
    big = box(0, 0, 100, 100)
    kept = _shrink_sam_overbox(big, 1.0, 5.0)  # 10000 m²
    assert [round(v, 6) for v in kept.bounds] == [5.0, 5.0, 95.0, 95.0]
