"""Local React preview + a read-only strategy API; no real-data endpoints yet."""
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import yaml

from backend.strategies import StrategyDisplay, load_strategy_display

app = FastAPI(title="둘이서은퇴 · 로컬 API", version="0.1.0", docs_url="/api/docs",
              redoc_url=None, openapi_url="/api/openapi.json")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])


@app.middleware("http")
async def local_boundary(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        origin = request.headers.get("origin")
        if (origin and urlparse(origin).netloc != request.headers.get("host")) or request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Cross-origin requests are not supported"}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "demo", "real_data_connected": False}


@app.get("/api/strategies", response_model=list[StrategyDisplay])
def strategies():
    try:
        return load_strategy_display()
    except (OSError, yaml.YAMLError, ValidationError, KeyError, TypeError, AttributeError):
        raise HTTPException(status_code=503, detail="전략 규칙을 확인할 수 없습니다. 잠시 후 다시 시도해 주세요.") from None


dist = Path(__file__).resolve().parents[1] / "web" / "dist"
if dist.is_dir():
    # Only the compiled public UI is served. No project-root mount, no uploads.
    # Hash routing keeps unknown paths a 404 instead of masking API failures.
    app.mount("/", StaticFiles(directory=dist, html=True), name="web")
