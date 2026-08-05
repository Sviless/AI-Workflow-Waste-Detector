"""Configuration and generation-mode resolution.

Reads environment variables to decide which generation mode is available.
The LLM API key is never printed or exposed anywhere in the app; only its
presence (True/False) is surfaced.

A tiny, dependency-free ``.env`` loader is included so a user can create a
local ``.env`` file with ``LLM_API_KEY=...`` without installing extra packages.
Template Engine Mode never needs any of this — the app runs with no key.
"""

from __future__ import annotations

import os

# Environment variable names that may hold the LLM API key. The first one that
# is set wins, so a Gemini user can simply set GEMINI_API_KEY or GOOGLE_API_KEY.
LLM_API_KEY_ENV = "LLM_API_KEY"
API_KEY_ENV_NAMES = ("LLM_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")
# Optional: which LLM vendor to target (defaults to Google Gemini).
LLM_PROVIDER_ENV = "LLM_PROVIDER"
# Optional: which model to request.
LLM_MODEL_ENV = "LLM_MODEL"

# Defaults for the built-in Google Gemini integration.
DEFAULT_LLM_PROVIDER = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

# Canonical mode names used across the app.
MODE_TEMPLATE = "Template Engine Mode"
MODE_LLM = "LLM Enhanced Mode"
AVAILABLE_MODES = [MODE_TEMPLATE, MODE_LLM]


def _load_dotenv(path: str = ".env") -> None:
    """Load simple KEY=VALUE lines from a local .env file if it exists.

    This is intentionally minimal (no external dependency). Existing
    environment variables are never overwritten. Lines starting with '#'
    and blank lines are ignored.
    """
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Do not overwrite a value already provided by the environment.
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        # A malformed or unreadable .env should never crash the app.
        pass


# Load .env once at import time so os.environ is populated for the app.
_load_dotenv()


def get_api_key() -> str:
    """Return the LLM API key from the environment, or an empty string.

    Checks each name in :data:`API_KEY_ENV_NAMES` in order so a Gemini user can
    set any of ``LLM_API_KEY``, ``GEMINI_API_KEY``, or ``GOOGLE_API_KEY``.
    The caller should treat this as a secret and never display it.
    """
    for name in API_KEY_ENV_NAMES:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def has_api_key() -> bool:
    """Return True if an LLM API key is configured (without exposing it)."""
    return bool(get_api_key())


def get_llm_provider_name() -> str:
    """Return the configured LLM vendor (defaults to Google Gemini)."""
    return os.environ.get(LLM_PROVIDER_ENV, DEFAULT_LLM_PROVIDER).strip() or DEFAULT_LLM_PROVIDER


def get_llm_model_name() -> str:
    """Return the configured model, falling back to the default Gemini model."""
    return os.environ.get(LLM_MODEL_ENV, "").strip() or DEFAULT_GEMINI_MODEL


def resolve_mode(requested_mode: str) -> tuple[str, bool]:
    """Resolve the effective generation mode.

    Returns a tuple of ``(effective_mode, fell_back)``. If LLM Enhanced Mode
    is requested but no API key is configured, the effective mode falls back
    to Template Engine Mode and ``fell_back`` is True.
    """
    if requested_mode == MODE_LLM and not has_api_key():
        return MODE_TEMPLATE, True
    if requested_mode not in AVAILABLE_MODES:
        return MODE_TEMPLATE, False
    return requested_mode, False
