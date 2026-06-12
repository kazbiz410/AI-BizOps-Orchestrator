import traceback

from fastapi import FastAPI


startup_error = None

try:
    from app.main import app as vercel_app

    app = vercel_app
except Exception as exc:  # pragma: no cover - deployment fallback path
    startup_error = f"{exc.__class__.__name__}: {exc}"
    traceback.print_exc()

    app = FastAPI(
        title="AI BizOps Orchestrator API",
        version="0.1.0",
        description="Fallback app for deployment diagnostics",
    )

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {
            "status": "error",
            "environment": "unknown",
            "startup_error": startup_error or "unknown error",
        }

    @app.get("/{path:path}")
    def deployment_error(path: str) -> dict[str, str]:
        return {
            "status": "error",
            "path": path,
            "startup_error": startup_error or "unknown error",
        }
