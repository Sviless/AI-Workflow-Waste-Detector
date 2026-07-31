"""Workflow waste scoring and automation readiness scoring logic.

All scores are on a 0-100 scale.
  * Waste score: higher means MORE waste (worse).
  * Automation readiness score: higher means MORE ready to automate (better).
"""

from __future__ import annotations

from .utils import count_items, has_content

# Keywords that suggest rework / instability inside free-text fields.
_REWORK_KEYWORDS = (
    "rework",
    "redo",
    "correct",
    "error",
    "mistake",
    "repeat",
    "back and forth",
    "loop",
    "revision",
    "revise",
    "fix",
)

_RISK_KEYWORDS = (
    "risk",
    "single point",
    "compliance",
    "audit",
    "security",
    "manual",
    "outage",
    "failure",
    "gap",
    "unclear",
)

# Maximum points each waste component can contribute. Documented here so the
# score stays transparent: the total possible is capped at 100 overall.
WASTE_WEIGHTS: dict[str, int] = {
    "Process steps": 15,
    "Handoffs": 15,
    "Approvals": 12,
    "Waiting points": 16,
    "Duplicate trackers/reports": 15,
    "Meetings": 10,
    "Rework indicators": 16,
    "Tool complexity": 8,
    "Risk level": 10,
    "Unclear ownership": 8,
    "Documentation clarity": 7,
}

# Each automation readiness check is worth this many points (10 checks x 10).
AUTOMATION_CHECK_POINTS = 10


def _keyword_hits(text: str | None, keywords: tuple[str, ...]) -> int:
    """Count how many keywords appear in a block of text."""
    if not text:
        return 0
    lowered = text.lower()
    return sum(1 for kw in keywords if kw in lowered)


def _cap(value: float, ceiling: float) -> float:
    """Clamp a value to the range [0, ceiling]."""
    return max(0.0, min(value, ceiling))


def compute_waste_score(wf: dict) -> dict:
    """Compute the workflow waste score (0-100, higher = more waste).

    The score aggregates weighted signals drawn from the workflow inputs.
    Each component is capped so no single factor dominates.
    """
    steps = count_items(wf.get("steps_today"))
    handoffs = count_items(wf.get("handoffs"))
    approvals = count_items(wf.get("approval_steps"))
    waiting = count_items(wf.get("waiting_points"))
    duplicates = count_items(wf.get("duplicate_trackers"))
    meetings = count_items(wf.get("meetings"))
    tools = count_items(wf.get("tools_systems"))

    rework_hits = count_items(wf.get("rework")) + _keyword_hits(
        wf.get("pain_points"), _REWORK_KEYWORDS
    )
    risk_hits = count_items(wf.get("known_risks")) + _keyword_hits(
        wf.get("pain_points"), _RISK_KEYWORDS
    )

    # Ownership clarity: unclear if no owner defined.
    owner_defined = has_content(wf.get("workflow_owner"))
    # Documentation clarity: based on description richness.
    documented = has_content(wf.get("current_description")) and steps >= 3

    breakdown = {
        "Process steps": _cap((steps - 5) * 1.5 if steps > 5 else 0, WASTE_WEIGHTS["Process steps"]),
        "Handoffs": _cap(handoffs * 3, WASTE_WEIGHTS["Handoffs"]),
        "Approvals": _cap(approvals * 3, WASTE_WEIGHTS["Approvals"]),
        "Waiting points": _cap(waiting * 4, WASTE_WEIGHTS["Waiting points"]),
        "Duplicate trackers/reports": _cap(duplicates * 5, WASTE_WEIGHTS["Duplicate trackers/reports"]),
        "Meetings": _cap(meetings * 2.5, WASTE_WEIGHTS["Meetings"]),
        "Rework indicators": _cap(rework_hits * 4, WASTE_WEIGHTS["Rework indicators"]),
        "Tool complexity": _cap((tools - 3) * 2 if tools > 3 else 0, WASTE_WEIGHTS["Tool complexity"]),
        "Risk level": _cap(risk_hits * 2.5, WASTE_WEIGHTS["Risk level"]),
        "Unclear ownership": 0 if owner_defined else WASTE_WEIGHTS["Unclear ownership"],
        "Documentation clarity": 0 if documented else WASTE_WEIGHTS["Documentation clarity"],
    }

    # Round each component so the transparent breakdown reads cleanly.
    breakdown = {name: round(points, 1) for name, points in breakdown.items()}

    raw = sum(breakdown.values())
    score = int(round(_cap(raw, 100)))
    status, color = waste_status(score)

    return {
        "score": score,
        "status": status,
        "color": color,
        "breakdown": breakdown,
        "breakdown_max": dict(WASTE_WEIGHTS),
        "signals": {
            "steps": steps,
            "handoffs": handoffs,
            "approvals": approvals,
            "waiting": waiting,
            "duplicates": duplicates,
            "meetings": meetings,
            "tools": tools,
            "rework_hits": rework_hits,
            "risk_hits": risk_hits,
            "owner_defined": owner_defined,
            "documented": documented,
        },
    }


def waste_status(score: int) -> tuple[str, str]:
    """Map a waste score to a status label and a color name."""
    if score <= 30:
        return "Low Waste / Healthy Workflow", "green"
    if score <= 60:
        return "Moderate Waste / Improvement Recommended", "orange"
    return "High Waste / Redesign Recommended", "red"


def compute_automation_readiness(wf: dict) -> dict:
    """Compute the automation readiness score (0-100, higher = more ready)."""
    steps = count_items(wf.get("steps_today"))
    rework = count_items(wf.get("rework"))
    risks = count_items(wf.get("known_risks"))

    checks = {
        "Clear inputs": has_content(wf.get("inputs_required")),
        "Clear outputs": has_content(wf.get("outputs_produced")),
        "Stable process steps": steps >= 3,
        "Defined owner": has_content(wf.get("workflow_owner")),
        "Defined trigger": has_content(wf.get("current_description")),
        "Defined success criteria": has_content(wf.get("future_state_outcome")),
        "Low ambiguity": _keyword_hits(wf.get("pain_points"), ("unclear", "confus", "ambig")) == 0,
        "Low exception rate": rework <= 1,
        "Clear data source": has_content(wf.get("tools_systems")),
        "Standardized tracker or form": count_items(wf.get("duplicate_trackers")) <= 1,
    }

    # Each of the 10 checks is worth 10 points.
    points = sum(AUTOMATION_CHECK_POINTS for passed in checks.values() if passed)

    # Light penalty for high risk which increases exception handling complexity.
    penalty = min(risks * 3, 15)
    score = int(round(_cap(points - penalty, 100)))
    status, color = automation_status(score)

    return {
        "score": score,
        "status": status,
        "color": color,
        "checks": checks,
        "points_per_check": AUTOMATION_CHECK_POINTS,
        "checks_passed": sum(1 for passed in checks.values() if passed),
        "checks_total": len(checks),
        "risk_penalty": penalty,
    }


def automation_status(score: int) -> tuple[str, str]:
    """Map an automation readiness score to a status label and color name."""
    if score >= 80:
        return "Ready for Automation", "green"
    if score >= 50:
        return "Simplify Before Automating", "orange"
    return "Not Ready for Automation", "red"


def improvement_priority(waste_score: int, automation_score: int) -> tuple[str, str]:
    """Derive an overall improvement priority label and color."""
    if waste_score >= 61:
        return "High Priority", "red"
    if waste_score >= 31:
        return "Medium Priority", "orange"
    if automation_score < 50:
        return "Medium Priority", "orange"
    return "Low Priority", "green"


def should_simplify_first(waste: dict, automation: dict) -> bool:
    """Return True when waste is high but automation readiness is low."""
    return waste["score"] >= 61 and automation["score"] < 50
