from __future__ import annotations

from app.api.schemas import AnalyticsResult
from app.core.config import Settings


def compute_analytics(
    panel_count: int,
    usable_area_m2: float,
    settings: Settings,
    agent_summary: str = "",
) -> AnalyticsResult:
    capacity = round(panel_count * settings.panel_kw, 2)
    annual_gen = round(capacity * settings.peak_sun_hours * settings.derate, 1)
    cost = round(capacity * settings.cost_per_kw_usd, 2)
    savings = round(annual_gen * settings.tariff_per_kwh_usd, 2)
    roi = round(cost / savings, 2) if savings > 0 else None

    return AnalyticsResult(
        system_capacity_kw=capacity,
        annual_generation_kwh=annual_gen,
        estimated_cost_usd=cost,
        annual_savings_usd=savings,
        roi_years=roi,
        agent_summary=agent_summary,
        usable_area_m2=round(usable_area_m2, 2),
    )
