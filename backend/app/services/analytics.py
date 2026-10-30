from __future__ import annotations

from app.api.schemas import AnalyticsResult, Assumptions
from app.core.config import Settings


def resolve_settings(settings: Settings, assumptions: Assumptions | None) -> Settings:
    """Copy settings with per-audit overrides; validates grid/battery combo."""
    if assumptions is None:
        return settings
    if assumptions.grid_type not in ("ongrid", "offgrid"):
        raise ValueError("grid_type must be 'ongrid' or 'offgrid'")
    if assumptions.grid_type == "offgrid" and assumptions.battery_kwh <= 0:
        raise ValueError("offgrid systems need battery_kwh > 0")
    update = {}
    for field in (
        "panel_kw",
        "panel_width_m",
        "panel_height_m",
        "cost_per_kw_usd",
        "tariff_per_kwh_usd",
        "peak_sun_hours",
        "battery_price_per_kwh_usd",
    ):
        value = getattr(assumptions, field)
        if value is not None:
            update[field] = value
    return settings.model_copy(update=update)


def compute_analytics(
    panel_count: int,
    usable_area_m2: float,
    settings: Settings,
    agent_summary: str = "",
    assumptions: Assumptions | None = None,
) -> AnalyticsResult:
    eff = resolve_settings(settings, assumptions)
    grid = assumptions.grid_type if assumptions else "ongrid"
    battery_kwh = round(assumptions.battery_kwh, 2) if assumptions else 0.0

    capacity = round(panel_count * eff.panel_kw, 2)
    annual_gen = round(capacity * eff.peak_sun_hours * eff.derate, 1)
    battery_cost = round(battery_kwh * eff.battery_price_per_kwh_usd, 2)
    cost = round(capacity * eff.cost_per_kw_usd + battery_cost, 2)
    savings = round(annual_gen * eff.tariff_per_kwh_usd, 2)
    roi = round(cost / savings, 2) if savings > 0 else None

    return AnalyticsResult(
        system_capacity_kw=capacity,
        annual_generation_kwh=annual_gen,
        estimated_cost_usd=cost,
        annual_savings_usd=savings,
        roi_years=roi,
        agent_summary=agent_summary,
        usable_area_m2=round(usable_area_m2, 2),
        battery_kwh=battery_kwh,
        battery_cost_usd=battery_cost,
        grid_type=grid,
    )
