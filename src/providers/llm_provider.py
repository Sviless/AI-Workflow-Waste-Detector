"""LLM Enhanced Mode provider (Google Gemini).

This provider adds a real LLM integration while keeping the app runnable with
**no** API key. Behavior:

  * If no API key is configured, it transparently falls back to Template Engine
    Mode and flags that fallback in the analysis metadata.
  * If a key *is* configured, it builds a strong prompt, calls Google Gemini in
    :meth:`_call_llm`, and merges the model's structured JSON response onto the
    reliable Template Engine baseline (so scores and structure are always
    present, and any Gemini-authored section text overrides the baseline).

The Gemini SDK (``google-genai``) is imported lazily inside the call, so the
app still works even if the package is not installed — it simply falls back to
Template Engine Mode. No network call is made unless a key is configured.
"""

from __future__ import annotations

import json

from .. import config
from ..template_engine import SECTION_ORDER
from .base_provider import GenerationProvider
from .template_provider import TemplateEngineProvider

# ---------------------------------------------------------------------------
# TARGET output schema for a future LLM integration.
#
# NOTE: This is the *target* JSON shape we want a future LLM to return so its
# response can be parsed programmatically. The current app does NOT make an API
# call yet and still renders text/Markdown from Template Engine Mode — this
# schema simply documents the contract the prompt asks the model to follow so
# that parsing logic can be added later without changing the prompt again.
#
# Every value is intentionally empty here; it exists only to describe the shape
# (object vs. array vs. string) of each field to the model.
# ---------------------------------------------------------------------------
TARGET_JSON_SCHEMA: dict = {
    "executive_summary": "",
    "current_state_summary": "",
    "lean_waste_analysis": [],
    "six_s_assessment": {},
    "bottleneck_analysis": [],
    "ownership_handoff_analysis": [],
    "rework_duplication_analysis": [],
    "meeting_reporting_waste": [],
    "risk_control_gaps": [],
    "automation_readiness_assessment": "",
    "recommended_future_state_workflow": [],
    "standard_work_checklist": [],
    "improvement_action_plan": [],
    "quick_wins": [],
    "longer_term_improvements": [],
    "suggested_metrics": [],
    "before_after_narrative": "",
    "final_summary": "",
}

# Maps each TARGET_JSON_SCHEMA key to the rendered section title it fills in.
SCHEMA_TO_SECTION: dict = {
    "executive_summary": "Executive Summary",
    "current_state_summary": "Current-State Workflow Summary",
    "lean_waste_analysis": "Lean Waste Analysis",
    "six_s_assessment": "5S/6S Workflow Assessment",
    "bottleneck_analysis": "Bottleneck Analysis",
    "ownership_handoff_analysis": "Ownership and Handoff Analysis",
    "rework_duplication_analysis": "Rework and Duplication Analysis",
    "meeting_reporting_waste": "Meeting and Reporting Waste Analysis",
    "risk_control_gaps": "Risk and Control Gaps",
    "automation_readiness_assessment": "Automation Readiness Assessment",
    "recommended_future_state_workflow": "Recommended Future-State Workflow",
    "standard_work_checklist": "Standard Work Checklist",
    "improvement_action_plan": "Improvement Action Plan",
    "quick_wins": "Quick Wins",
    "longer_term_improvements": "Longer-Term Improvements",
    "suggested_metrics": "Suggested Metrics",
    "before_after_narrative": "Before and After Narrative",
    "final_summary": "Final Workflow Improvement Summary",
}


class LLMEnhancedProvider(GenerationProvider):
    """Provider that will use an external LLM once one is configured."""

    name = config.MODE_LLM

    def __init__(self, fallback: GenerationProvider | None = None) -> None:
        # Reuse the local provider for fallback and for guaranteed structure.
        self.fallback = fallback or TemplateEngineProvider()
        # Populated with the last provider error message (for status display).
        self._last_error: str = ""

    def is_available(self) -> bool:
        """LLM mode is 'available' only when an API key is configured."""
        return config.has_api_key()

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------
    def build_prompt(self, input_data: dict) -> str:
        """Build a strong, provider-neutral prompt for a future LLM call.

        The prompt asks the model to perform the same Lean/6S analysis the
        Template Engine performs and to return a single structured JSON object
        matching :data:`TARGET_JSON_SCHEMA`. That schema is a *target* format
        for future parsing — the current app makes no API call and still
        renders text output from Template Engine Mode — but pinning the
        contract now keeps the prompt stable once real parsing is added.
        """
        # Section titles the Template Engine already produces, listed so the
        # model covers the same analytical ground even though the JSON keys
        # below are the authoritative output contract.
        sections_list = "\n".join(f"  {i}. {t}" for i, t in enumerate(SECTION_ORDER, 1))
        workflow_json = json.dumps(input_data, indent=2, ensure_ascii=False)

        # The exact JSON skeleton the model must fill in and return. Rendering
        # it from the shared TARGET_JSON_SCHEMA keeps the prompt and the future
        # parser aligned on one source of truth.
        target_json = json.dumps(TARGET_JSON_SCHEMA, indent=2, ensure_ascii=False)

        return f"""You are an expert Lean / 6S operational-excellence consultant and
workflow automation engineer. Analyze the workflow described below and produce a
single, structured workflow improvement package.

ROLE AND TONE
- Be professional, specific, and evidence-based.
- Base every finding on the workflow input; never invent facts not implied by it.
- Prefer concrete, actionable language over generic advice.

ANALYSIS REQUIREMENTS
1. Lean waste analysis — evaluate the workflow against the Lean waste categories:
   Waiting, Overprocessing, Excess motion, Defects or rework, Overproduction,
   Inventory or backlog, Transportation or unnecessary handoffs, Underutilized
   talent, Unclear ownership, and Manual work that could be simplified.
2. 5S / 6S workflow assessment — assess the workflow across Sort, Set in Order,
   Shine, Standardize, Sustain, and Safety.
3. Structural analysis — identify bottlenecks, ownership and handoff issues,
   rework and duplication, meeting and reporting waste, and risk/control gaps.
4. Workflow Waste Score — an integer 0-100 (higher = more waste) with a status
   band: 0-30 Low Waste / Healthy Workflow, 31-60 Moderate Waste / Improvement
   Recommended, 61-100 High Waste / Redesign Recommended.
5. Automation Readiness Score — an integer 0-100 (higher = more ready) with a
   status band: 80-100 Ready for Automation, 50-79 Simplify Before Automating,
   0-49 Not Ready for Automation.
6. Future-state design — recommend a redesigned workflow, standard work,
   an action plan, quick wins, longer-term improvements, and metrics.

RECOMMENDATION LOGIC (MANDATORY)
- If Workflow Waste is HIGH (score 61-100) AND Automation Readiness is LOW
  (score 0-49), you MUST recommend simplification BEFORE automation. State
  clearly: "Do not automate this workflow yet. Simplify, standardize, and
  clarify ownership first, then reassess automation readiness."
- Otherwise, recommend the proportionate next step (targeted improvement or,
  when the workflow is healthy and ready, automation).
- Reflect this recommendation in "executive_summary",
  "automation_readiness_assessment", and "final_summary".

OUTPUT FORMAT (STRICT)
- Return ONLY a single valid JSON object. No prose, no Markdown, no code fences
  before or after the JSON.
- Use exactly the keys shown below, with the same value types (string, array,
  or object). Do not add or rename keys.
- For array fields, return a list of clear, self-contained items (strings or
  small objects with descriptive keys).
- For "six_s_assessment", return an object keyed by each S (Sort, Set in Order,
  Shine, Standardize, Sustain, Safety) with a short assessment string for each.
- Numeric scores are integers. Do not include a score inside the JSON unless a
  field for it is present; instead, weave the scores and their status bands into
  "executive_summary", "automation_readiness_assessment", and "final_summary".

REQUIRED JSON STRUCTURE (fill in every field):
{target_json}

For reference, the equivalent analysis sections the package should cover are:
{sections_list}

WORKFLOW INPUT (JSON)
{workflow_json}
"""

    # ------------------------------------------------------------------
    # Real API call (Google Gemini)
    # ------------------------------------------------------------------
    def _call_llm(self, prompt: str) -> str | None:
        """Send ``prompt`` to the configured LLM and return the raw response.

        Currently targets Google Gemini via the ``google-genai`` SDK. Any
        failure (missing key, missing SDK, or network/API error) is recorded in
        ``self._last_error`` and returns ``None`` so the provider falls back to
        Template Engine Mode instead of crashing the app.
        """
        api_key = config.get_api_key()
        if not api_key:
            self._last_error = "No API key configured."
            return None

        provider = config.get_llm_provider_name().lower()
        if provider in ("gemini", "google", "google-gemini", "generic"):
            return self._call_gemini(prompt, api_key, config.get_llm_model_name())

        self._last_error = f"Unsupported LLM provider: {provider!r}."
        return None

    def _call_gemini(self, prompt: str, api_key: str, model: str) -> str | None:
        """Call the Google Gemini API and return the raw JSON text response."""
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            self._last_error = (
                "The 'google-genai' package is not installed. "
                "Run: pip install google-genai"
            )
            return None

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:  # noqa: BLE001 - never crash the app on API errors
            self._last_error = f"Gemini API error: {exc}"
            return None

        text = getattr(response, "text", None)
        if not text:
            self._last_error = "Gemini returned an empty response."
            return None
        return text

    @staticmethod
    def _extract_json(raw: str) -> dict | None:
        """Parse a JSON object from ``raw``, tolerating stray text or fences."""
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, TypeError):
            pass
        if isinstance(raw, str):
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end > start:
                try:
                    data = json.loads(raw[start : end + 1])
                    return data if isinstance(data, dict) else None
                except json.JSONDecodeError:
                    return None
        return None

    @staticmethod
    def _to_markdown(value: object) -> str:
        """Render a schema value (string, list, or object) as Markdown."""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            lines: list[str] = []
            for item in value:
                if isinstance(item, dict):
                    parts = [
                        f"**{str(k).replace('_', ' ').title()}:** {v}"
                        for k, v in item.items()
                    ]
                    lines.append("- " + "; ".join(parts))
                else:
                    lines.append(f"- {item}")
            return "\n".join(lines)
        if isinstance(value, dict):
            return "\n".join(
                f"- **{str(k).replace('_', ' ').title()}:** {v}"
                for k, v in value.items()
            )
        return str(value)

    def _parse_llm_response(self, raw: str, input_data: dict) -> dict:
        """Merge the Gemini JSON response onto the local baseline structure.

        Starting from the Template Engine analysis guarantees a complete,
        renderable structure with locally computed scores. Any section the model
        returns overrides the corresponding baseline section, so the app stays
        robust even if the response is partial.
        """
        ctx = self.fallback.generate_workflow_analysis(input_data)
        data = self._extract_json(raw)
        if not data:
            ctx["meta"]["requested_mode"] = self.name
            ctx["meta"]["fell_back"] = True
            ctx["meta"]["llm_status"] = "parse_error"
            return ctx

        for key, section in SCHEMA_TO_SECTION.items():
            value = data.get(key)
            if value in (None, "", [], {}):
                continue
            rendered = self._to_markdown(value)
            if rendered:
                ctx["sections"][section] = rendered

        ctx["meta"]["mode"] = self.name
        ctx["meta"]["requested_mode"] = self.name
        ctx["meta"]["fell_back"] = False
        ctx["meta"]["llm_status"] = "ok"
        ctx["meta"]["llm_model"] = config.get_llm_model_name()
        return ctx

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def generate_workflow_analysis(self, input_data: dict) -> dict:
        # 1) No key configured -> use Template Engine Mode transparently.
        if not self.is_available():
            ctx = self.fallback.generate_workflow_analysis(input_data)
            ctx["meta"]["requested_mode"] = self.name
            ctx["meta"]["fell_back"] = True
            ctx["meta"]["llm_status"] = "no_api_key"
            return ctx

        # 2) Key configured -> build the prompt and call the LLM.
        prompt = self.build_prompt(input_data)
        self._last_error = ""
        raw = self._call_llm(prompt)

        if raw is None:
            # The call failed (missing SDK, API error, etc.): fall back cleanly
            # to Template Engine Mode and surface why for the status indicator.
            ctx = self.fallback.generate_workflow_analysis(input_data)
            ctx["meta"]["requested_mode"] = self.name
            ctx["meta"]["fell_back"] = True
            ctx["meta"]["llm_status"] = "call_failed"
            ctx["meta"]["llm_error"] = self._last_error
            return ctx

        # 3) A response was returned -> merge it onto the baseline.
        return self._parse_llm_response(raw, input_data)
