"""Generic sample workflows and the canonical input field definitions.

All content here is fictional and generic. It contains no confidential,
proprietary, or company-specific information.
"""

from __future__ import annotations

# Canonical field definitions used by the input form, scoring, and exports.
# Each tuple: (key, label, is_list, placeholder/help)
FIELD_DEFS: list[tuple[str, str, bool, str]] = [
    ("workflow_name", "Workflow name", False, "e.g., Weekly Status Reporting"),
    ("workflow_owner", "Workflow owner", False, "e.g., Operations Program Manager"),
    ("workflow_purpose", "Workflow purpose", False, "Why this workflow exists"),
    ("team_function", "Team or function", False, "e.g., Program Management Office"),
    ("current_description", "Current workflow description", False,
     "Describe how the workflow runs today"),
    ("steps_today", "Step-by-step workflow today", True, "One step per line"),
    ("inputs_required", "Inputs required", True, "One input per line"),
    ("outputs_produced", "Outputs produced", True, "One output per line"),
    ("tools_systems", "Tools or systems used", True, "One tool per line"),
    ("stakeholders", "Stakeholders involved", True, "One stakeholder per line"),
    ("approval_steps", "Approval steps", True, "One approval per line"),
    ("handoffs", "Handoffs between people or teams", True, "One handoff per line"),
    ("waiting_points", "Waiting points or delays", True, "One delay per line"),
    ("rework", "Rework or repeated corrections", True, "One rework item per line"),
    ("duplicate_trackers", "Duplicate trackers or duplicate reporting", True,
     "One duplicate tracker per line"),
    ("meetings", "Meetings required by the workflow", True, "One meeting per line"),
    ("pain_points", "Pain points", True, "One pain point per line"),
    ("known_risks", "Known risks", True, "One risk per line"),
    ("future_state_outcome", "Desired future-state outcome", False,
     "What a better future state looks like"),
    ("additional_notes", "Additional notes", False, "Anything else worth capturing"),
]

FIELD_KEYS = [f[0] for f in FIELD_DEFS]
FIELD_LABELS = {f[0]: f[1] for f in FIELD_DEFS}
LIST_FIELDS = [f[0] for f in FIELD_DEFS if f[2]]


def empty_workflow() -> dict:
    """Return an empty workflow dict with all keys initialized to blank."""
    return {key: "" for key in FIELD_KEYS}


SAMPLE_WORKFLOWS: list[dict] = [
    {
        "workflow_name": "Weekly Status Reporting",
        "workflow_owner": "Operations Program Manager",
        "workflow_purpose": (
            "Provide leadership with a weekly view of project progress, risks, and blockers."
        ),
        "team_function": "Program Management Office",
        "current_description": (
            "Every week, individual contributors update personal trackers, then a program "
            "manager collects them, reconciles conflicting numbers, and rebuilds a summary "
            "deck by hand before a leadership review meeting."
        ),
        "steps_today": (
            "Contributors update personal spreadsheets\n"
            "Team leads copy updates into a shared tracker\n"
            "Program manager reconciles conflicting entries\n"
            "Program manager builds a summary slide deck\n"
            "Deck is emailed for pre-review\n"
            "Leadership review meeting held\n"
            "Follow-up notes distributed manually"
        ),
        "inputs_required": (
            "Individual task updates\n"
            "Risk notes\n"
            "Milestone dates"
        ),
        "outputs_produced": (
            "Summary slide deck\n"
            "Leadership review notes\n"
            "Action item list"
        ),
        "tools_systems": (
            "Spreadsheet tool\n"
            "Presentation tool\n"
            "Email\n"
            "Chat app"
        ),
        "stakeholders": (
            "Individual contributors\n"
            "Team leads\n"
            "Program manager\n"
            "Leadership"
        ),
        "approval_steps": (
            "Team lead review of updates\n"
            "Program manager sign-off on deck"
        ),
        "handoffs": (
            "Contributors to team leads\n"
            "Team leads to program manager\n"
            "Program manager to leadership"
        ),
        "waiting_points": (
            "Waiting for late updates\n"
            "Waiting for deck review\n"
            "Waiting for meeting slot"
        ),
        "rework": (
            "Reconciling conflicting numbers\n"
            "Correcting outdated milestone dates\n"
            "Rebuilding slides after late changes"
        ),
        "duplicate_trackers": (
            "Personal spreadsheets\n"
            "Shared tracker\n"
            "Slide deck restating the same data"
        ),
        "meetings": (
            "Team sync\n"
            "Pre-review alignment\n"
            "Leadership review"
        ),
        "pain_points": (
            "Manual reconciliation is slow and error prone\n"
            "Unclear which number is the source of truth\n"
            "Repeated copy and paste work"
        ),
        "known_risks": (
            "Single point of failure on the program manager\n"
            "Reporting errors reach leadership\n"
            "Late updates hide real risks"
        ),
        "future_state_outcome": (
            "One shared source of truth that auto-generates the summary, with no manual "
            "reconciliation and clear ownership of each data field."
        ),
        "additional_notes": (
            "The team has asked to automate the deck, but the underlying data is not yet "
            "consistent."
        ),
    },
    {
        "workflow_name": "New Vendor Onboarding",
        "workflow_owner": "Procurement Coordinator",
        "workflow_purpose": (
            "Onboard a new supplier so they can be issued purchase orders and paid."
        ),
        "team_function": "Procurement Operations",
        "current_description": (
            "A requester emails procurement, who manually chases documents, routes approvals "
            "over email, and re-keys the same vendor details into several systems."
        ),
        "steps_today": (
            "Requester emails a vendor request\n"
            "Procurement requests vendor documents\n"
            "Documents reviewed for completeness\n"
            "Finance approves banking details\n"
            "Legal reviews contract terms\n"
            "Vendor entered into finance system\n"
            "Vendor entered into procurement system\n"
            "Confirmation emailed to requester"
        ),
        "inputs_required": (
            "Vendor request form\n"
            "Tax documents\n"
            "Banking details\n"
            "Signed contract"
        ),
        "outputs_produced": (
            "Approved vendor record\n"
            "Vendor ID\n"
            "Onboarding confirmation"
        ),
        "tools_systems": (
            "Email\n"
            "Finance system\n"
            "Procurement system\n"
            "Shared drive"
        ),
        "stakeholders": (
            "Requester\n"
            "Procurement coordinator\n"
            "Finance\n"
            "Legal\n"
            "Vendor"
        ),
        "approval_steps": (
            "Finance approval of banking details\n"
            "Legal approval of contract terms\n"
            "Procurement manager final approval"
        ),
        "handoffs": (
            "Requester to procurement\n"
            "Procurement to finance\n"
            "Procurement to legal\n"
            "Procurement to systems entry"
        ),
        "waiting_points": (
            "Waiting for vendor documents\n"
            "Waiting for finance approval\n"
            "Waiting for legal review"
        ),
        "rework": (
            "Re-requesting missing documents\n"
            "Correcting mismatched vendor details across systems"
        ),
        "duplicate_trackers": (
            "Email threads\n"
            "Procurement intake spreadsheet"
        ),
        "meetings": (
            "Weekly procurement triage"
        ),
        "pain_points": (
            "Same data re-keyed into multiple systems\n"
            "Approvals get lost in email\n"
            "No clear status visibility for the requester"
        ),
        "known_risks": (
            "Incorrect banking details create payment risk\n"
            "Compliance gap if documents are incomplete"
        ),
        "future_state_outcome": (
            "A single intake form that routes approvals automatically and syncs vendor data "
            "to both systems without re-keying."
        ),
        "additional_notes": (
            "Volume is moderate but spikes at quarter end."
        ),
    },
    {
        "workflow_name": "Support Ticket Triage",
        "workflow_owner": "Support Team Lead",
        "workflow_purpose": (
            "Route incoming customer support tickets to the right team quickly."
        ),
        "team_function": "Customer Support",
        "current_description": (
            "Incoming tickets are manually read and categorized, then assigned. Categories are "
            "clear and stable, and inputs and outputs are well defined."
        ),
        "steps_today": (
            "Ticket arrives in the queue\n"
            "Agent reads and categorizes ticket\n"
            "Agent assigns to a specialist team\n"
            "Specialist team resolves the ticket\n"
            "Resolution logged and closed"
        ),
        "inputs_required": (
            "Customer message\n"
            "Product area\n"
            "Priority"
        ),
        "outputs_produced": (
            "Categorized ticket\n"
            "Assigned owner\n"
            "Resolution record"
        ),
        "tools_systems": (
            "Ticketing system"
        ),
        "stakeholders": (
            "Customer\n"
            "Triage agent\n"
            "Specialist teams"
        ),
        "approval_steps": "",
        "handoffs": (
            "Triage agent to specialist team"
        ),
        "waiting_points": (
            "Waiting in queue before triage"
        ),
        "rework": "",
        "duplicate_trackers": "",
        "meetings": (
            "Daily standup"
        ),
        "pain_points": (
            "Triage is repetitive and consumes agent time"
        ),
        "known_risks": (
            "Mis-categorization delays resolution"
        ),
        "future_state_outcome": (
            "Automated categorization and routing so agents focus on complex tickets."
        ),
        "additional_notes": (
            "Category rules are well documented and rarely change."
        ),
    },
]
