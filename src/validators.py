"""Input validation, missing field detection, and quality warnings."""

from __future__ import annotations

from .utils import clean_text, count_items, has_content

# Fields that must be present for a meaningful analysis.
REQUIRED_FIELDS = {
    "workflow_name": "Workflow name",
    "current_description": "Current workflow description",
    "steps_today": "Step-by-step workflow today",
}

# Fields that strongly improve analysis quality when provided.
RECOMMENDED_FIELDS = {
    "workflow_owner": "Workflow owner",
    "workflow_purpose": "Workflow purpose",
    "inputs_required": "Inputs required",
    "outputs_produced": "Outputs produced",
    "tools_systems": "Tools or systems used",
    "handoffs": "Handoffs between people or teams",
    "future_state_outcome": "Desired future-state outcome",
}


def validate_inputs(wf: dict) -> dict:
    """Validate workflow inputs.

    Returns a dict with:
      * ok: bool - whether required fields are present
      * errors: list[str] - blocking issues
      * warnings: list[str] - quality suggestions
    """
    errors: list[str] = []
    warnings: list[str] = []

    for key, label in REQUIRED_FIELDS.items():
        if not has_content(wf.get(key)):
            errors.append(f"Missing required field: {label}.")

    for key, label in RECOMMENDED_FIELDS.items():
        if not has_content(wf.get(key)):
            warnings.append(f"Consider adding: {label} for a richer analysis.")

    # Quality checks.
    if has_content(wf.get("steps_today")) and count_items(wf.get("steps_today")) < 3:
        warnings.append(
            "Only a few workflow steps were entered. Add more detail for a stronger waste analysis."
        )

    description = clean_text(wf.get("current_description"))
    if description and len(description) < 40:
        warnings.append(
            "The workflow description is quite short. A fuller description improves the analysis."
        )

    # If no waste-signal fields are provided, the analysis will be thin.
    signal_fields = ("handoffs", "waiting_points", "approval_steps",
                     "duplicate_trackers", "meetings", "rework")
    if not any(has_content(wf.get(field)) for field in signal_fields):
        warnings.append(
            "No handoffs, delays, approvals, duplicates, meetings, or rework were entered. "
            "Add at least one of these so the waste analysis has something to work with."
        )

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}
