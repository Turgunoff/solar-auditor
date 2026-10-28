from __future__ import annotations

import logging
from typing import Protocol

from app.api.schemas import AnalyticsResult
from app.core.config import Settings
from app.services.disclaimer import DISCLAIMER_SHORT
from app.services.meta_client import MetaAPIError, MetaAPINotReady, get_meta_client

logger = logging.getLogger(__name__)


class AgentReportService(Protocol):
    def summarize(
        self,
        analytics: AnalyticsResult,
        panel_count: int,
        obstacle_count: int,
        provider_out: list[str] | None = None,
    ) -> tuple[str, str]:
        """Returns (summary_text, provider)."""
        ...


def _append_disclaimer(text: str) -> str:
    t = (text or "").strip()
    if DISCLAIMER_SHORT in t:
        return t
    return f"{t} {DISCLAIMER_SHORT}".strip()


class MockAgentReporter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def summarize(
        self,
        analytics: AnalyticsResult,
        panel_count: int,
        obstacle_count: int,
        provider_out: list[str] | None = None,
    ) -> tuple[str, str]:
        roi = (
            f"{analytics.roi_years} years"
            if analytics.roi_years is not None
            else "N/A"
        )
        area = analytics.usable_area_m2 or 0.0
        glass = panel_count * self.settings.panel_width_m * self.settings.panel_height_m
        text = (
            f"Layout engine packed {panel_count} × {self.settings.panel_kw * 1000:.0f}W "
            f"modules ({self.settings.panel_width_m}×{self.settings.panel_height_m} m, "
            f"~{glass:.0f} m² glass) on ~{area:.0f} m² usable SAM roof after "
            f"{obstacle_count} obstacle buffer(s) → {analytics.system_capacity_kw} kWp. "
            f"Generation (~{analytics.annual_generation_kwh:,.0f} kWh/yr) and payback "
            f"({roi}) use fixed {self.settings.peak_sun_hours:.0f} peak-sun-hours and "
            f"${self.settings.tariff_per_kwh_usd:.2f}/kWh — not measured irradiance. "
            f"Muse Image is concept art; trust the layout overlay for module count. "
            f"Next: on-site pitch/azimuth, structure, shading, and utility check."
        )
        return _append_disclaimer(text), "mock"


class MuseTextAgentReporter:
    def __init__(self, settings: Settings, fallback: MockAgentReporter) -> None:
        self.settings = settings
        self.fallback = fallback
        self.client = get_meta_client(settings)

    def summarize(
        self,
        analytics: AnalyticsResult,
        panel_count: int,
        obstacle_count: int,
        provider_out: list[str] | None = None,
    ) -> tuple[str, str]:
        facts = {
            "panel_count": panel_count,
            "capacity_kw": analytics.system_capacity_kw,
            "annual_kwh": analytics.annual_generation_kwh,
            "cost_usd": analytics.estimated_cost_usd,
            "savings_usd": analytics.annual_savings_usd,
            "roi_years": analytics.roi_years,
            "obstacle_count": obstacle_count,
            "usable_area_m2": analytics.usable_area_m2,
        }
        try:
            text = self.client.engineering_summary(facts)
            return _append_disclaimer(text), f"meta-{self.settings.muse_text_model}"
        except (MetaAPINotReady, MetaAPIError) as exc:
            logger.warning("Muse text live path unavailable: %s", exc)
            if not self.settings.allow_mock_fallback:
                raise
            text, _ = self.fallback.summarize(
                analytics, panel_count, obstacle_count, provider_out
            )
            return text, f"meta-{self.settings.muse_text_model}+mock-fallback"


def get_agent_service(settings: Settings) -> AgentReportService:
    mock = MockAgentReporter(settings)
    if settings.mock_forced():
        return mock
    return MuseTextAgentReporter(settings, mock)
