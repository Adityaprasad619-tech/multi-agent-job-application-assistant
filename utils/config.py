"""
Configuration Manager
=====================
Centralizes all environment variable loading and validation.

Design Decisions:
- Single source of truth for all config values.
- Fails fast with clear error messages if required vars are missing.
- Uses @dataclass for type safety and immutability.
- Loaded once at startup, then injected where needed (no global reads scattered across code).
- Auth provider config: defaults to "local" (SQLite+bcrypt), switchable to "clerk".
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Resolve .env path relative to project root (one level above utils/)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_PATH)


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration loaded from environment."""

    # --- Groq LLM ---
    groq_api_key: str
    groq_model_name: str

    # --- USAJobs API ---
    usajobs_api_key: str
    usajobs_email: str

    # --- Authentication ---
    auth_provider: str              # "local" or "clerk"
    clerk_secret_key: str           # only needed if auth_provider == "clerk"
    clerk_publishable_key: str      # only needed if auth_provider == "clerk"

    # --- Development ---
    test_mode: bool                 # True = mock agent outputs, no Groq calls

    # --- Paths ---
    project_root: Path
    db_path: Path
    log_dir: Path


def load_config() -> AppConfig:
    """
    Load and validate all configuration from environment variables.

    Raises
    ------
    SystemExit
        If any required environment variable is missing.
    """
    missing: list[str] = []

    def _require(var_name: str) -> str:
        value = os.getenv(var_name, "").strip()
        if not value:
            missing.append(var_name)
            return ""
        return value

    groq_api_key = _require("GROQ_API_KEY")
    usajobs_api_key = _require("USAJOBS_API_KEY")
    usajobs_email = _require("USAJOBS_EMAIL")

    if missing:
        print(
            f"\n❌  Missing required environment variables: {', '.join(missing)}\n"
            f"   Copy .env.example → .env and fill in the values.\n"
        )
        sys.exit(1)

    groq_model = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile").strip()

    # --- Auth config ---
    auth_provider = os.getenv("AUTH_PROVIDER", "local").strip().lower()
    clerk_secret = os.getenv("CLERK_SECRET_KEY", "").strip()
    clerk_pub = os.getenv("CLERK_PUBLISHABLE_KEY", "").strip()

    # Validate Clerk keys only when Clerk is the chosen provider
    if auth_provider == "clerk" and (not clerk_secret or not clerk_pub):
        print(
            "\n❌  AUTH_PROVIDER=clerk but CLERK_SECRET_KEY / CLERK_PUBLISHABLE_KEY are missing.\n"
            "   Set them in .env or switch to AUTH_PROVIDER=local.\n"
        )
        sys.exit(1)

    # --- Development ---
    test_mode = os.getenv("TEST_MODE", "false").strip().lower() in ("true", "1", "yes")

    # Derived paths
    db_path_env = os.getenv("DATABASE_PATH", "database/job_search.db").strip()
    db_path = Path(db_path_env)
    if not db_path.is_absolute():
        db_path = _PROJECT_ROOT / db_path

    log_dir = _PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    return AppConfig(
        groq_api_key=groq_api_key,
        groq_model_name=groq_model,
        usajobs_api_key=usajobs_api_key,
        usajobs_email=usajobs_email,
        auth_provider=auth_provider,
        clerk_secret_key=clerk_secret,
        clerk_publishable_key=clerk_pub,
        test_mode=test_mode,
        project_root=_PROJECT_ROOT,
        db_path=db_path,
        log_dir=log_dir,
    )
