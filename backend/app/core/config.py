import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during scaffold stage
    def load_dotenv(*_args: object, **_kwargs: object) -> None:
        return None


CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parents[2]
REPO_ROOT = CURRENT_FILE.parents[3]

load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


def _normalize_supabase_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    if normalized.endswith("/rest/v1"):
        return normalized[: -len("/rest/v1")]
    return normalized


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    environment: str = os.getenv("ENVIRONMENT", "development")
    supabase_url: str = _normalize_supabase_url(os.getenv("SUPABASE_URL", ""))
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    slack_incoming_webhook_url: str = os.getenv("SLACK_INCOMING_WEBHOOK_URL", "")
    cors_allow_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv(
                "CORS_ALLOW_ORIGINS",
                "http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:3001,http://localhost:3001",
            )
        )
    )


settings = Settings()
