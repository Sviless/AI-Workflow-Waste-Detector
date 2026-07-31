"""Template Engine Mode provider.

Thin wrapper around the existing local generation logic in
``template_engine.py`` (which already reuses scoring, validators, and utils).
This provider always works and never needs an API key. It preserves all 18
output sections exactly as before.
"""

from __future__ import annotations

from ..config import MODE_TEMPLATE
from ..template_engine import generate_analysis
from .base_provider import GenerationProvider


class TemplateEngineProvider(GenerationProvider):
    """Local, rule-based generation provider (the default)."""

    name = MODE_TEMPLATE

    def is_available(self) -> bool:
        # Local generation is always available.
        return True

    def generate_workflow_analysis(self, input_data: dict) -> dict:
        ctx = generate_analysis(input_data)
        # Record which mode actually produced the result.
        ctx["meta"]["mode"] = self.name
        ctx["meta"]["requested_mode"] = self.name
        ctx["meta"]["fell_back"] = False
        return ctx
