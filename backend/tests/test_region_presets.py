"""Region presets: illustrative sun-hours/tariff defaults per region."""

import pytest

from app.api.schemas import Assumptions
from app.core.config import Settings
from app.services.analytics import REGION_PRESETS, compute_analytics


def test_region_applies_sun_and_tariff():
    s = Settings(use_mock=True)
    uz = REGION_PRESETS["uzbekistan"]
    res = compute_analytics(10, 50.0, s, assumptions=Assumptions(region="uzbekistan"))
    assert res.region == "uzbekistan"
    expected_kwh = round(4.0 * uz["peak_sun_hours"] * s.derate, 1)
    assert res.annual_generation_kwh == expected_kwh
    assert res.annual_savings_usd == round(expected_kwh * uz["tariff_per_kwh_usd"], 2)


def test_explicit_fields_win_over_region():
    s = Settings(use_mock=True)
    res = compute_analytics(
        10,
        50.0,
        s,
        assumptions=Assumptions(region="uzbekistan", tariff_per_kwh_usd=0.25),
    )
    assert res.annual_savings_usd == round(res.annual_generation_kwh * 0.25, 2)


def test_unknown_region_rejected():
    s = Settings(use_mock=True)
    with pytest.raises(ValueError, match="region"):
        compute_analytics(10, 50.0, s, assumptions=Assumptions(region="atlantis"))


def test_global_region_keeps_server_defaults():
    s = Settings(use_mock=True)
    res = compute_analytics(10, 50.0, s, assumptions=Assumptions(region="global"))
    assert res.region == "global"
    assert res.annual_generation_kwh == round(4.0 * s.peak_sun_hours * s.derate, 1)
