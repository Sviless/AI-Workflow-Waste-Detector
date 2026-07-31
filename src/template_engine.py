"""Template Engine Mode generation logic.

This module produces a full workflow improvement package using local Python
templates and rule-based analysis only. No external APIs or network calls are
used. The architecture is intentionally structured so that an "LLM Enhanced
Mode" can later be added behind the same ``generate_analysis`` interface.
"""

from __future__ import annotations

from .scoring import (
    compute_automation_readiness,
    compute_waste_score,
    improvement_priority,
    should_simplify_first,
)
from .utils import (
    clean_text,
    count_items,
    first_line,
    parse_list,
    timestamp,
    to_bullets,
    to_numbered,
)

GENERATION_MODE = "Template Engine Mode"

# Ordered list of the 18 output sections.
SECTION_ORDER = [
    "Executive Summary",
    "Current-State Workflow Summary",
    "Lean Waste Analysis",
    "5S/6S Workflow Assessment",
    "Bottleneck Analysis",
    "Ownership and Handoff Analysis",
    "Rework and Duplication Analysis",
    "Meeting and Reporting Waste Analysis",
    "Risk and Control Gaps",
    "Automation Readiness Assessment",
    "Recommended Future-State Workflow",
    "Standard Work Checklist",
    "Improvement Action Plan",
    "Quick Wins",
    "Longer-Term Improvements",
    "Suggested Metrics",
    "Before and After Narrative",
    "Final Workflow Improvement Summary",
]


# ---------------------------------------------------------------------------
# Structured analysis builders
# ---------------------------------------------------------------------------

def build_waste_findings(wf: dict, signals: dict) -> list[dict]:
    """Generate Lean-categorized waste findings from workflow signals."""
    findings: list[dict] = []

    def add(category, observation, impact, recommendation, severity):
        findings.append(
            {
                "category": category,
                "observation": observation,
                "impact": impact,
                "recommendation": recommendation,
                "severity": severity,
            }
        )

    if signals["waiting"] > 0:
        add(
            "Waiting",
            f"{signals['waiting']} waiting point(s) or delay(s) were identified.",
            "Idle time extends cycle time and hides true capacity.",
            "Map the queue, set service-level targets, and pull work rather than push it.",
            "High" if signals["waiting"] >= 3 else "Medium",
        )

    if signals["steps"] > 8:
        add(
            "Overprocessing",
            f"The workflow has {signals['steps']} steps, which is long for a single flow.",
            "Long step chains add cycle time and increase the chance of errors and delays.",
            "Combine or remove low-value steps and question any step that does not change the output.",
            "Medium",
        )

    if signals["approvals"] > 2:
        add(
            "Overprocessing",
            f"{signals['approvals']} approval steps are required.",
            "Excess approvals add delay without proportional risk reduction.",
            "Apply risk-based approvals; remove or auto-approve low-risk cases.",
            "Medium",
        )

    if signals["tools"] > 3:
        add(
            "Excess motion",
            f"Work spans {signals['tools']} tools or systems.",
            "Context switching between systems wastes effort and invites errors.",
            "Consolidate tools or integrate them so data flows without manual switching.",
            "Medium",
        )

    if signals["rework_hits"] > 0:
        add(
            "Defects or rework",
            "Rework, corrections, or repeated fixes were reported.",
            "Rework loops consume capacity and erode trust in outputs.",
            "Add validation at the source and define a single source of truth.",
            "High" if signals["rework_hits"] >= 3 else "Medium",
        )

    if signals["duplicates"] > 1:
        add(
            "Overproduction",
            f"{signals['duplicates']} duplicate trackers or reports restate the same data.",
            "Producing the same information more than once is pure waste.",
            "Retire duplicate trackers and generate reports from one dataset.",
            "High" if signals["duplicates"] >= 3 else "Medium",
        )

    if signals["waiting"] > 0 or signals["duplicates"] > 1:
        add(
            "Inventory or backlog",
            "Work items or updates accumulate between steps.",
            "Backlogs mask problems and delay feedback.",
            "Limit work-in-progress and make backlog size visible.",
            "Medium",
        )

    if signals["handoffs"] > 2:
        add(
            "Transportation or unnecessary handoffs",
            f"{signals['handoffs']} handoffs move work between people or teams.",
            "Every handoff risks dropped context, delay, and rework.",
            "Reduce handoffs, clarify ownership, and standardize what is passed along.",
            "High" if signals["handoffs"] >= 4 else "Medium",
        )

    if signals["rework_hits"] > 0 or signals["duplicates"] > 1:
        add(
            "Underutilized talent",
            "Skilled staff spend time on manual reconciliation and copy-paste work.",
            "Talent is diverted from higher-value problem solving.",
            "Automate mechanical steps once the process is simplified and standardized.",
            "Medium",
        )

    if not signals["owner_defined"]:
        add(
            "Unclear ownership",
            "No single workflow owner is clearly defined.",
            "Unclear ownership slows decisions and creates single points of failure.",
            "Assign one accountable owner and document decision rights.",
            "High",
        )

    manual_signal = (
        "manual" in (wf.get("pain_points") or "").lower()
        or "manual" in (wf.get("current_description") or "").lower()
        or signals["duplicates"] > 0
    )
    if manual_signal:
        add(
            "Manual work that could be simplified",
            "Manual, repetitive steps appear throughout the workflow.",
            "Manual steps are slow and error prone at scale.",
            "Simplify and standardize first, then evaluate automation.",
            "Medium",
        )

    return findings


def build_five_s_assessment(wf: dict, signals: dict) -> dict:
    """Produce a 5S/6S assessment mapped to digital workflow concepts."""
    assessment: dict[str, str] = {}

    sort_targets = []
    if signals["approvals"] > 2:
        sort_targets.append("redundant approval steps")
    if signals["meetings"] > 2:
        sort_targets.append("meetings that could be async updates")
    if signals["duplicates"] > 1:
        sort_targets.append("duplicate trackers and reports")
    assessment["Sort"] = (
        "Review and remove: " + ", ".join(sort_targets) + "."
        if sort_targets
        else "No obvious unnecessary steps, reports, or meetings detected. Confirm each still adds value."
    )

    assessment["Set in Order"] = (
        f"Clarify sequence and ownership across {signals['handoffs']} handoff(s). "
        "Define who owns each step and what information passes between them."
        if signals["handoffs"] > 0
        else "Confirm the step sequence is optimal and each step has a clear owner."
    )

    assessment["Shine"] = (
        "Clean up unclear or outdated elements: "
        + first_line(
            wf.get("pain_points"),
            "clarify confusing steps and remove stale artifacts.",
        )
    )

    assessment["Standardize"] = (
        "Introduce standard work: a shared template, a single tracker with common fields, "
        "naming conventions, and a checklist so the workflow runs the same way every time."
    )

    assessment["Sustain"] = (
        "Establish a recurring review cadence, a small metrics dashboard, and clear "
        "accountability so improvements hold over time."
    )

    risk_note = first_line(wf.get("known_risks"), "unclear handoffs or missing controls")
    assessment["Safety"] = (
        f"Address risk exposure such as {risk_note.lower()}. "
        "Remove single points of failure and document critical controls."
    )

    return assessment


def build_future_state(wf: dict, signals: dict) -> list[str]:
    """Generate a cleaner future-state workflow tailored to detected waste."""
    steps = [
        "Capture the trigger event in a single intake form with required fields validated at entry.",
        "Maintain one shared source of truth; eliminate personal and duplicate trackers.",
        "Assign a single accountable owner and clear decision rights for each step.",
    ]
    # Add targeted steps only for the waste signals actually detected.
    if signals["duplicates"] > 1:
        steps.append(
            f"Retire the {signals['duplicates']} duplicate trackers/reports and report from the shared dataset only."
        )
    if signals["approvals"] > 2:
        steps.append(
            f"Replace the {signals['approvals']} serial approvals with risk-based approval so only exceptions need sign-off."
        )
    if signals["handoffs"] > 2:
        steps.append(
            f"Reduce the {signals['handoffs']} handoffs; when a handoff is required, pass standardized, complete information."
        )
    if signals["waiting"] > 0:
        steps.append(
            "Set service-level targets at each queue and limit work-in-progress to shrink waiting time."
        )
    if signals["meetings"] > 1:
        steps.append(
            "Replace status meetings with an always-current shared view; meet only to make decisions or handle exceptions."
        )
    if signals["rework_hits"] > 0:
        steps.append(
            "Validate data at the point of entry to break rework loops before outputs are produced."
        )
    if not signals["owner_defined"]:
        steps.append("Publish a RACI so ownership and decision rights are unambiguous.")
    steps.append("Auto-generate outputs and reports from the single dataset.")
    steps.append("Track a small set of metrics and review them on a fixed cadence to sustain the gains.")
    return steps


def build_checklist(wf: dict, signals: dict) -> list[dict]:
    """Generate a standard work checklist."""
    items = [
        ("Confirm the workflow trigger and entry criteria are defined", "Standardize"),
        ("Verify required inputs are present and validated at intake", "Standardize"),
        ("Confirm a single accountable owner is assigned", "Set in Order"),
        ("Use the single shared source of truth (no side trackers)", "Sort"),
        ("Follow the documented step sequence", "Set in Order"),
        ("Apply risk-based approvals only where required", "Sort"),
        ("Complete required fields before any handoff", "Set in Order"),
        ("Generate outputs from the shared dataset, not by re-keying", "Standardize"),
        ("Log exceptions and rework for review", "Sustain"),
        ("Review metrics on the agreed cadence", "Sustain"),
        ("Confirm critical controls and documentation are in place", "Safety"),
    ]
    return [{"item": text, "category": cat} for text, cat in items]


def build_action_plan(wf: dict, findings: list[dict], simplify_first: bool) -> list[dict]:
    """Generate an improvement action plan derived from the findings."""
    actions: list[dict] = []

    def add(title, category, effort, impact, horizon, owner):
        actions.append(
            {
                "title": title,
                "category": category,
                "effort": effort,
                "impact": impact,
                "horizon": horizon,
                "owner": owner,
            }
        )

    owner = clean_text(wf.get("workflow_owner")) or "Assign an owner"

    if simplify_first:
        add(
            "Simplify and standardize the workflow before automating",
            "Manual work that could be simplified",
            "Medium",
            "High",
            "Quick Win",
            owner,
        )

    # Derive actions from the top findings.
    for finding in findings:
        horizon = "Quick Win" if finding["severity"] != "High" else "Longer-Term"
        effort = "Low" if finding["severity"] == "Low" else "Medium"
        add(
            finding["recommendation"],
            finding["category"],
            effort,
            finding["severity"],
            horizon,
            owner,
        )

    # De-duplicate by title while preserving order.
    seen = set()
    unique_actions = []
    for action in actions:
        if action["title"] not in seen:
            seen.add(action["title"])
            unique_actions.append(action)
    return unique_actions


def split_quick_wins(actions: list[dict]) -> tuple[list[str], list[str]]:
    """Split action items into quick wins and longer-term improvements."""
    quick = [a["title"] for a in actions if a["horizon"] == "Quick Win"]
    longer = [a["title"] for a in actions if a["horizon"] != "Quick Win"]
    if not quick:
        quick = [
            "Consolidate duplicate trackers into one shared source of truth.",
            "Assign a single accountable owner for the workflow.",
        ]
    if not longer:
        longer = [
            "Integrate tools so data flows without manual re-keying.",
            "Establish a metrics dashboard and recurring review cadence.",
        ]
    return quick, longer


def build_metrics(wf: dict) -> list[str]:
    """Suggest a small set of metrics to track improvement."""
    return [
        "Cycle time (trigger to completion)",
        "Touch time vs. wait time ratio",
        "Number of handoffs per item",
        "Rework rate (percent of items requiring correction)",
        "Number of active trackers or reports",
        "On-time completion rate",
        "Approval turnaround time",
    ]


# ---------------------------------------------------------------------------
# Section renderers (Markdown text)
# ---------------------------------------------------------------------------

def _render_sections(ctx: dict) -> dict:
    """Render all 18 Markdown sections from the analysis context."""
    wf = ctx["workflow"]
    waste = ctx["waste"]
    automation = ctx["automation"]
    signals = waste["signals"]
    findings = ctx["waste_findings"]
    sections: dict[str, str] = {}

    name = clean_text(wf.get("workflow_name")) or "Unnamed Workflow"
    owner = clean_text(wf.get("workflow_owner")) or "Unassigned"

    # 1. Executive Summary
    simplify_note = ""
    if ctx["simplify_first"]:
        simplify_note = (
            "\n\n> **Important:** Do not automate this workflow yet. "
            "Simplify, standardize, and clarify ownership first."
        )
    sections["Executive Summary"] = (
        f"**Workflow:** {name}  \n"
        f"**Owner:** {owner}  \n"
        f"**Purpose:** {clean_text(wf.get('workflow_purpose')) or 'Not specified.'}\n\n"
        f"This workflow scored **{waste['score']}/100** on the waste scale "
        f"(*{waste['status']}*) and **{automation['score']}/100** on automation readiness "
        f"(*{automation['status']}*). Overall improvement priority is "
        f"**{ctx['priority'][0]}**. The analysis below identifies "
        f"{len(findings)} waste finding(s) and a recommended future-state design."
        f"{simplify_note}"
    )

    # 2. Current-State Workflow Summary
    sections["Current-State Workflow Summary"] = (
        f"{clean_text(wf.get('current_description')) or 'No description provided.'}\n\n"
        f"**Team or function:** {clean_text(wf.get('team_function')) or 'Not specified.'}\n\n"
        f"**Steps today:**\n{to_numbered(parse_list(wf.get('steps_today')))}\n\n"
        f"**Inputs required:**\n{to_bullets(parse_list(wf.get('inputs_required')))}\n\n"
        f"**Outputs produced:**\n{to_bullets(parse_list(wf.get('outputs_produced')))}\n\n"
        f"**Tools or systems:**\n{to_bullets(parse_list(wf.get('tools_systems')))}\n\n"
        f"**Stakeholders:**\n{to_bullets(parse_list(wf.get('stakeholders')))}"
    )

    # 3. Lean Waste Analysis
    if findings:
        lines = []
        for f in findings:
            lines.append(
                f"### {f['category']} ({f['severity']})\n"
                f"- **Observation:** {f['observation']}\n"
                f"- **Impact:** {f['impact']}\n"
                f"- **Recommendation:** {f['recommendation']}"
            )
        sections["Lean Waste Analysis"] = "\n\n".join(lines)
    else:
        sections["Lean Waste Analysis"] = (
            "No significant Lean waste signals were detected from the inputs provided."
        )

    # 4. 5S/6S Workflow Assessment
    fives = ctx["fives_assessment"]
    sections["5S/6S Workflow Assessment"] = "\n\n".join(
        f"**{key}:** {value}" for key, value in fives.items()
    )

    # 5. Bottleneck Analysis
    bottlenecks = []
    if signals["waiting"] > 0:
        bottlenecks.append(f"{signals['waiting']} explicit waiting point(s) create queue delays.")
    if signals["approvals"] > 2:
        bottlenecks.append(f"{signals['approvals']} approvals serialize the flow.")
    if signals["handoffs"] > 2:
        bottlenecks.append(f"{signals['handoffs']} handoffs introduce coordination delay.")
    if not signals["owner_defined"]:
        bottlenecks.append("Unclear ownership slows decisions at every step.")
    sections["Bottleneck Analysis"] = (
        to_bullets(bottlenecks)
        if bottlenecks
        else "No major bottlenecks detected. Monitor cycle time to confirm."
    )

    # 6. Ownership and Handoff Analysis
    sections["Ownership and Handoff Analysis"] = (
        f"**Owner:** {owner}. "
        + ("Ownership is defined.\n\n" if signals["owner_defined"] else "No clear owner is assigned; this is a key gap.\n\n")
        + f"**Handoffs ({signals['handoffs']}):**\n{to_bullets(parse_list(wf.get('handoffs')))}\n\n"
        + "Each handoff should pass complete, standardized information to reduce dropped context and rework."
    )

    # 7. Rework and Duplication Analysis
    sections["Rework and Duplication Analysis"] = (
        f"**Rework / repeated corrections:**\n{to_bullets(parse_list(wf.get('rework')))}\n\n"
        f"**Duplicate trackers or reports:**\n{to_bullets(parse_list(wf.get('duplicate_trackers')))}\n\n"
        + (
            "Rework and duplication are strong candidates for elimination. Establish a single "
            "source of truth and validate data at the point of entry."
        )
    )

    # 8. Meeting and Reporting Waste Analysis
    sections["Meeting and Reporting Waste Analysis"] = (
        f"**Meetings required ({signals['meetings']}):**\n{to_bullets(parse_list(wf.get('meetings')))}\n\n"
        + (
            "Consider replacing status meetings with an always-current shared view. Reserve "
            "meetings for decisions and exception handling, and generate reports automatically "
            "from a single dataset."
        )
    )

    # 9. Risk and Control Gaps
    sections["Risk and Control Gaps"] = (
        f"**Known risks:**\n{to_bullets(parse_list(wf.get('known_risks')))}\n\n"
        + (
            "Mitigate single points of failure by documenting the process and cross-training. "
            "Add lightweight controls (validation, audit trail) at critical steps."
        )
    )

    # 10. Automation Readiness Assessment
    checks = automation["checks"]
    check_lines = "\n".join(
        f"- {'✅' if passed else '⬜'} {name}" for name, passed in checks.items()
    )
    readiness_note = (
        "\n\n> Do not automate this workflow yet. Simplify, standardize, and clarify ownership first."
        if ctx["simplify_first"]
        else ""
    )
    sections["Automation Readiness Assessment"] = (
        f"**Score:** {automation['score']}/100 — *{automation['status']}*\n\n"
        f"{check_lines}{readiness_note}"
    )

    # 11. Recommended Future-State Workflow
    sections["Recommended Future-State Workflow"] = (
        f"**Desired outcome:** {clean_text(wf.get('future_state_outcome')) or 'Not specified.'}\n\n"
        f"**Proposed future-state steps:**\n{to_numbered(ctx['future_state_steps'])}"
    )

    # 12. Standard Work Checklist
    sections["Standard Work Checklist"] = "\n".join(
        f"- [ ] {c['item']} _( {c['category']} )_" for c in ctx["checklist"]
    )

    # 13. Improvement Action Plan
    if ctx["action_items"]:
        action_lines = []
        for i, a in enumerate(ctx["action_items"], start=1):
            action_lines.append(
                f"{i}. **{a['title']}**  \n"
                f"   Category: {a['category']} | Effort: {a['effort']} | "
                f"Impact: {a['impact']} | Horizon: {a['horizon']} | Owner: {a['owner']}"
            )
        sections["Improvement Action Plan"] = "\n".join(action_lines)
    else:
        sections["Improvement Action Plan"] = "No action items generated."

    # 14. Quick Wins
    sections["Quick Wins"] = to_bullets(ctx["quick_wins"])

    # 15. Longer-Term Improvements
    sections["Longer-Term Improvements"] = to_bullets(ctx["longer_term"])

    # 16. Suggested Metrics
    sections["Suggested Metrics"] = to_bullets(ctx["metrics"])

    # 17. Before and After Narrative
    sections["Before and After Narrative"] = (
        "**Before:** " + (clean_text(wf.get("current_description")) or "The current workflow relies on manual steps, duplicate trackers, and multiple handoffs.")
        + "\n\n**After:** With a single source of truth, clear ownership, risk-based approvals, "
        "and automated outputs, the workflow becomes faster, more reliable, and easier to sustain. "
        f"Waste is expected to drop from the current {waste['score']}/100 toward a healthier range, "
        "and the process becomes a stronger candidate for automation once stabilized."
    )

    # 18. Final Workflow Improvement Summary
    sections["Final Workflow Improvement Summary"] = (
        f"- **Waste score:** {waste['score']}/100 ({waste['status']})\n"
        f"- **Automation readiness:** {automation['score']}/100 ({automation['status']})\n"
        f"- **Improvement priority:** {ctx['priority'][0]}\n"
        f"- **Top waste categories:** "
        + (", ".join(sorted({f['category'] for f in findings})) if findings else "None detected")
        + "\n"
        f"- **Recommended next step:** "
        + (
            "Simplify, standardize, and clarify ownership before automating."
            if ctx["simplify_first"]
            else "Proceed with the prioritized action plan and monitor the suggested metrics."
        )
    )

    return sections


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_analysis(wf: dict) -> dict:
    """Generate the full workflow improvement package for a workflow.

    Returns a structured dict containing scores, structured findings, and the
    18 rendered Markdown sections. This is the single interface an
    LLM-enhanced mode would later implement.
    """
    waste = compute_waste_score(wf)
    automation = compute_automation_readiness(wf)
    signals = waste["signals"]
    simplify_first = should_simplify_first(waste, automation)

    findings = build_waste_findings(wf, signals)
    fives = build_five_s_assessment(wf, signals)
    future_state = build_future_state(wf, signals)
    checklist = build_checklist(wf, signals)
    actions = build_action_plan(wf, findings, simplify_first)
    quick_wins, longer_term = split_quick_wins(actions)
    metrics = build_metrics(wf)

    ctx = {
        "workflow": wf,
        "meta": {"generated_at": timestamp(), "mode": GENERATION_MODE},
        "waste": waste,
        "automation": automation,
        "priority": improvement_priority(waste["score"], automation["score"]),
        "simplify_first": simplify_first,
        "waste_findings": findings,
        "fives_assessment": fives,
        "future_state_steps": future_state,
        "checklist": checklist,
        "action_items": actions,
        "quick_wins": quick_wins,
        "longer_term": longer_term,
        "metrics": metrics,
    }
    ctx["sections"] = _render_sections(ctx)
    return ctx
