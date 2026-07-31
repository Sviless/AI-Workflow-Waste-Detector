"""Generation providers package.

Exposes a small factory that returns the right provider for a requested mode.
Template Engine Mode is always the safe default and requires no API key.
"""

from __future__ import annotations

from .. import config
from .base_provider import GenerationProvider
from .llm_provider import LLMEnhancedProvider
from .template_provider import TemplateEngineProvider

__all__ = [
    "GenerationProvider",
    "TemplateEngineProvider",
    "LLMEnhancedProvider",
    "get_provider",
    "generate",
]


def get_provider(requested_mode: str) -> GenerationProvider:
    """Return a provider instance for the requested mode.

    LLM Enhanced Mode is returned only as a wrapper; if no API key is
    configured it falls back to Template Engine Mode at generation time.
    """
    if requested_mode == config.MODE_LLM:
        return LLMEnhancedProvider()
    return TemplateEngineProvider()


def generate(requested_mode: str, input_data: dict) -> dict:
    """Convenience helper: pick a provider and generate the analysis."""
    return get_provider(requested_mode).generate_workflow_analysis(input_data)
