import traceback
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


app = FastAPI(
    title="AI BizOps Orchestrator API",
    version="0.1.0",
    description="Backend API for AI BizOps Orchestrator v0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

startup_error: Optional[str] = None

try:
    from app.api.routes import router

    app.include_router(router)
except Exception as exc:  # pragma: no cover - deployment fallback path
    startup_error = f"{exc.__class__.__name__}: {exc}"
    traceback.print_exc()


@app.get("/health")
def health_check() -> dict[str, Optional[str]]:
    return {
        "status": "ok" if startup_error is None else "error",
        "environment": settings.environment,
        "startup_error": startup_error,
    }
