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

# Environment variable name for the (optional) LLM API key.
LLM_API_KEY_ENV = "LLM_API_KEY"
# Optional: which LLM vendor a future integration should target.
LLM_PROVIDER_ENV = "LLM_PROVIDER"
# Optional: which model a future integration should request.
LLM_MODEL_ENV = "LLM_MODEL"

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

    The caller should treat this as a secret and never display it.
    """
    return os.environ.get(LLM_API_KEY_ENV, "").strip()


def has_api_key() -> bool:
    """Return True if an LLM API key is configured (without exposing it)."""
    return bool(get_api_key())


def get_llm_provider_name() -> str:
    """Return the configured LLM vendor hint (e.g. 'openai'), or 'generic'."""
    return os.environ.get(LLM_PROVIDER_ENV, "generic").strip() or "generic"


def get_llm_model_name() -> str:
    """Return the configured model hint, or a neutral placeholder."""
    return os.environ.get(LLM_MODEL_ENV, "").strip()


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
