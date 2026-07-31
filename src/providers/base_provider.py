"""Provider interface for workflow analysis generation.

The app talks to a *provider* rather than calling template functions directly.
This keeps generation pluggable: today Template Engine Mode; tomorrow an
LLM-backed provider — both behind the same ``generate_workflow_analysis``
method returning the same structured analysis dict.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class GenerationProvider(ABC):
    """Abstract base class every generation provider must implement."""

    # Human-readable mode name shown in the UI and stored with the analysis.
    name: str = "Provider"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider can run in the current environment."""
        raise NotImplementedError

    @abstractmethod
    def generate_workflow_analysis(self, input_data: dict) -> dict:
        """Generate the full workflow improvement package.

        Args:
            input_data: The workflow input fields (a plain dict).

        Returns:
            A structured analysis context dict containing scores, structured
            findings, and the 18 rendered Markdown sections. The shape must be
            compatible with the app's rendering, storage, and exporters.
        """
        raise NotImplementedError
