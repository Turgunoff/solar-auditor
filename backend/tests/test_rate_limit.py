"""Rate limiter: expensive paths throttled, others untouched."""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from app.core.rate_limit import RateLimitMiddleware


def _app(per_minute=2):
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, per_minute=per_minute)

    @app.post("/api/process/upload")
    def heavy():
        return PlainTextResponse("ok")

    @app.get("/api/health")
    def light():
        return PlainTextResponse("ok")

    return TestClient(app, raise_server_exceptions=False)


def test_limited_path_throttled():
    client = _app(per_minute=2)
    assert client.post("/api/process/upload").status_code == 200
    assert client.post("/api/process/upload").status_code == 200
    r = client.post("/api/process/upload")
    assert r.status_code == 429
    assert "Rate limit" in r.json()["detail"]


def test_unlimited_path_passes():
    client = _app(per_minute=1)
    client.post("/api/process/upload")
    for _ in range(5):
        assert client.get("/api/health").status_code == 200
