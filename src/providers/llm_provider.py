"""LLM Enhanced Mode provider (future-ready).

This provider is prepared for a future LLM integration but requires **no** API
key for the app to run. Behavior:

  * If no ``LLM_API_KEY`` is configured, it transparently falls back to
    Template Engine Mode and flags that fallback in the analysis metadata.
  * If a key *is* configured, it builds a strong, provider-neutral prompt and
    calls :meth:`_call_llm` — the single, clearly marked place where a real
    API call (OpenAI, Azure OpenAI, Claude, or another vendor) would be added
    later. Until that call is implemented it returns ``None`` and the provider
    still falls back to Template Engine Mode so the app always produces output.

No external LLM SDKs are imported here, so there are no extra dependencies and
no network calls are made.
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


class LLMEnhancedProvider(GenerationProvider):
    """Provider that will use an external LLM once one is configured."""

    name = config.MODE_LLM

    def __init__(self, fallback: GenerationProvider | None = None) -> None:
        # Reuse the local provider for fallback and for guaranteed structure.
        self.fallback = fallback or TemplateEngineProvider()

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
    # Real API call goes here (future work)
    # ------------------------------------------------------------------
    def _call_llm(self, prompt: str) -> str | None:
        """Placeholder for a real LLM API call.

        A future integration would send ``prompt`` to the configured provider
        and return the raw text response. Keep this provider-neutral so it can
        target OpenAI, Azure OpenAI, Claude, or another vendor.

        Example (pseudocode) for a future implementation:

            api_key = config.get_api_key()          # never logged/printed
            vendor = config.get_llm_provider_name()  # e.g. "openai"
            model = config.get_llm_model_name()      # e.g. "gpt-4o-mini"
            # client = <vendor SDK>(api_key=api_key)
            # response = client.responses.create(model=model, input=prompt)
            # return response.output_text

        Until implemented, return None so the app falls back gracefully.
        """
        # No real call is made yet — no external dependency, no network access.
        return None

    def _parse_llm_response(self, raw: str, input_data: dict) -> dict:
        """Merge a future LLM JSON response onto the local baseline structure.

        Starting from the local (template) analysis guarantees a complete,
        renderable structure; any fields the LLM returns override the baseline.
        This keeps the app robust even if a future response is partial.

        NOTE: The prompt asks the model for :data:`TARGET_JSON_SCHEMA` (the
        target format for future parsing). This method is not exercised yet
        because no API call is made — the app still displays text/Markdown from
        Template Engine Mode. When a real call is wired up, extend the mapping
        below to translate the TARGET_JSON_SCHEMA keys into the ctx sections.
        The current key handling is intentionally conservative and backward
        compatible so nothing breaks before that work is done.
        """
        ctx = self.fallback.generate_workflow_analysis(input_data)
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return ctx  # Malformed response: keep the reliable baseline.

        if isinstance(data.get("sections"), dict):
            ctx["sections"].update(
                {k: v for k, v in data["sections"].items() if isinstance(v, str)}
            )
        if isinstance(data.get("waste_findings"), list):
            ctx["waste_findings"] = data["waste_findings"]
        if isinstance(data.get("waste_score"), int):
            ctx["waste"]["score"] = data["waste_score"]
        if isinstance(data.get("automation_score"), int):
            ctx["automation"]["score"] = data["automation_score"]
        if isinstance(data.get("simplify_first"), bool):
            ctx["simplify_first"] = data["simplify_first"]

        ctx["meta"]["mode"] = self.name
        ctx["meta"]["requested_mode"] = self.name
        ctx["meta"]["fell_back"] = False
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

        # 2) Key configured -> build the prompt and attempt the (future) call.
        prompt = self.build_prompt(input_data)
        raw = self._call_llm(prompt)

        if raw is None:
            # Call not implemented yet: fall back but keep the prompt for debugging.
            ctx = self.fallback.generate_workflow_analysis(input_data)
            ctx["meta"]["requested_mode"] = self.name
            ctx["meta"]["fell_back"] = True
            ctx["meta"]["llm_status"] = "not_implemented"
            ctx["meta"]["llm_prompt_preview"] = prompt[:1200]
            return ctx

        # 3) Future: a real response was returned -> merge onto the baseline.
        return self._parse_llm_response(raw, input_data)
