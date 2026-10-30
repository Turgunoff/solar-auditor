from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI mode
    use_mock: bool = True
    meta_api_key: str = ""
    meta_api_base_url: str = "https://api.meta.ai/v1"
    sam_model: str = "sam-3.1"
    muse_image_model: str = "muse-image-1.0"
    muse_text_model: str = "muse-spark-1.3"
    allow_mock_fallback: bool = True
    meta_timeout_seconds: float = 90.0
    mock_latency_ms: int = 350

    # Engineering constants
    panel_kw: float = 0.4
    peak_sun_hours: float = 1450.0
    cost_per_kw_usd: float = 800.0
    tariff_per_kwh_usd: float = 0.12
    panel_width_m: float = 1.7
    panel_height_m: float = 1.0
    setback_m: float = 0.5
    default_meters_per_pixel: float = 0.05
    # System losses (soiling, inverter, wiring, mismatch). 0.85 typical.
    derate: float = 0.85
    battery_price_per_kwh_usd: float = 300.0

    google_maps_api_key: str = ""

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Upload + retention guards
    max_upload_mb: int = 15
    min_upload_px: int = 64
    max_upload_mp: float = 50.0
    static_retention_days: int = 7
    rate_limit_per_minute: int = 60

    @property
    def sample_data_dir(self) -> Path:
        return BACKEND_ROOT / "sample_data"

    @property
    def static_dir(self) -> Path:
        return BACKEND_ROOT / "static"

    @property
    def uploads_dir(self) -> Path:
        return self.static_dir / "uploads"

    @property
    def renders_dir(self) -> Path:
        return self.static_dir / "renders"

    @property
    def exports_dir(self) -> Path:
        return self.static_dir / "exports"

    def ensure_dirs(self) -> None:
        for path in (
            self.sample_data_dir,
            self.uploads_dir,
            self.renders_dir,
            self.exports_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def has_api_key(self) -> bool:
        return bool(self.meta_api_key.strip())

    def mock_forced(self) -> bool:
        """True when we must not call live Meta APIs."""
        return self.use_mock or not self.has_api_key()

    def live_requested(self) -> bool:
        return (not self.use_mock) and self.has_api_key()

    def mode_label(self) -> str:
        return "live" if self.live_requested() else "mock"

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def public_status(self) -> Dict[str, Any]:
        """Safe for frontend — no secrets."""
        return {
            "mode": self.mode_label(),
            "use_mock": self.use_mock,
            "api_key_present": self.has_api_key(),
            "live_requested": self.live_requested(),
            "allow_mock_fallback": self.allow_mock_fallback,
            "meta_api_base_url": self.meta_api_base_url,
            "models": {
                "segmentation": self.sam_model,
                "render": self.muse_image_model,
                "agent": self.muse_text_model,
            },
            "ready_for_live": self.live_requested(),
            "google_maps_configured": bool(self.google_maps_api_key.strip()),
            "message": self._status_message(),
        }

    def _status_message(self) -> str:
        if self.use_mock:
            return "Running in mock mode (USE_MOCK=true). Full local demo works without Meta API."
        if not self.has_api_key():
            return "USE_MOCK=false but META_API_KEY is empty — staying on mock until key is set."
        if self.allow_mock_fallback:
            return "Live Meta API requested; mock fallback enabled if live calls fail."
        return "Live Meta API requested; mock fallback disabled — live failures will error."


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings


def clear_settings_cache() -> None:
    get_settings.cache_clear()
