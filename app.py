"""AI Workflow Waste Detector — Streamlit application.

Run with:  streamlit run app.py

This app analyzes a described workflow, identifies Lean waste, scores workflow
health and automation readiness, and generates a future-state improvement
package. It runs fully locally using Template Engine Mode (no API key required).
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src import config, db, exporters, providers
from src.sample_data import (
    FIELD_DEFS,
    FIELD_KEYS,
    LIST_FIELDS,
    SAMPLE_WORKFLOWS,
    empty_workflow,
)
from src.template_engine import SECTION_ORDER
from src.utils import file_timestamp, slugify
from src.validators import REQUIRED_FIELDS, validate_inputs


def _bridge_streamlit_secrets() -> None:
    """Copy known secrets into the environment for config to read.

    On Streamlit Community Cloud, an API key is provided via the app's Secrets
    rather than a local .env file. Mirroring those values into os.environ lets
    the dependency-free config module pick them up without importing Streamlit.
    """
    for name in ("LLM_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                 "LLM_PROVIDER", "LLM_MODEL"):
        try:
            if name in st.secrets and name not in os.environ:
                os.environ[name] = str(st.secrets[name])
        except Exception:
            # No secrets configured (e.g. local run) — safe to ignore.
            pass


_bridge_streamlit_secrets()

st.set_page_config(
    page_title="AI Workflow Waste Detector",
    page_icon="🧭",
    layout="wide",
)

# Ensure the database exists before anything else.
db.init_db()

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
for key in FIELD_KEYS:
    st.session_state.setdefault(key, "")
st.session_state.setdefault("analysis", None)
st.session_state.setdefault("selected_saved_id", None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def status_badge(color: str, text: str) -> None:
    """Render a colored status message."""
    if color == "green":
        st.success(text)
    elif color == "orange":
        st.warning(text)
    else:
        st.error(text)


def collect_form_values() -> dict:
    """Read current form values from session state into a workflow dict."""
    return {key: st.session_state.get(key, "") for key in FIELD_KEYS}


def load_sample(sample: dict) -> None:
    """Populate the form fields from a sample workflow and rerun."""
    for key in FIELD_KEYS:
        st.session_state[key] = sample.get(key, "")
    st.session_state["analysis"] = None


def clear_form() -> None:
    """Reset all form fields to empty and rerun."""
    blank = empty_workflow()
    for key in FIELD_KEYS:
        st.session_state[key] = blank[key]
    st.session_state["analysis"] = None


def render_scorecards(ctx: dict) -> None:
    """Render the top-line score cards for a generated analysis."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Workflow Waste Score", f"{ctx['waste']['score']}/100")
        st.progress(ctx["waste"]["score"] / 100)
        status_badge(ctx["waste"]["color"], ctx["waste"]["status"])
    with col2:
        st.metric("Automation Readiness", f"{ctx['automation']['score']}/100")
        st.progress(ctx["automation"]["score"] / 100)
        status_badge(ctx["automation"]["color"], ctx["automation"]["status"])
    with col3:
        st.metric("Improvement Priority", ctx["priority"][0])
        st.progress(1.0)
        status_badge(ctx["priority"][1], f"Priority: {ctx['priority'][0]}")

    if ctx["simplify_first"]:
        st.error(
            "⚠️ **Do not automate this workflow yet. "
            "Simplify, standardize, and clarify ownership first.**"
        )


def render_score_transparency(ctx: dict) -> None:
    """Show exactly how the waste and automation scores were calculated."""
    with st.expander("🔍 How these scores were calculated", expanded=False):
        wcol, acol = st.columns(2)

        with wcol:
            st.markdown("**Workflow Waste Score** (higher = more waste)")
            breakdown = ctx["waste"]["breakdown"]
            maxes = ctx["waste"].get("breakdown_max", {})
            waste_df = pd.DataFrame(
                [
                    {
                        "Component": name,
                        "Points": points,
                        "Max": maxes.get(name, ""),
                    }
                    for name, points in breakdown.items()
                ]
            )
            st.dataframe(waste_df, use_container_width=True, hide_index=True)
            st.caption(
                f"Total (capped at 100): **{ctx['waste']['score']}/100** — "
                f"{ctx['waste']['status']}"
            )

        with acol:
            st.markdown("**Automation Readiness** (higher = more ready)")
            checks = ctx["automation"]["checks"]
            pts = ctx["automation"].get("points_per_check", 10)
            auto_df = pd.DataFrame(
                [
                    {
                        "Readiness Check": name,
                        "Met": "Yes" if passed else "No",
                        "Points": pts if passed else 0,
                    }
                    for name, passed in checks.items()
                ]
            )
            st.dataframe(auto_df, use_container_width=True, hide_index=True)
            penalty = ctx["automation"].get("risk_penalty", 0)
            st.caption(
                f"Passed {ctx['automation'].get('checks_passed', 0)}/"
                f"{ctx['automation'].get('checks_total', len(checks))} checks · "
                f"risk penalty −{penalty} · "
                f"**{ctx['automation']['score']}/100** — {ctx['automation']['status']}"
            )


def render_analysis(ctx: dict, *, allow_save: bool) -> None:
    """Render a full analysis: scorecards, sections, and exports."""
    wf = ctx["workflow"]
    st.subheader(f"📋 {wf.get('workflow_name') or 'Unnamed Workflow'}")
    st.caption(f"Generated by {ctx['meta']['mode']} · {ctx['meta']['generated_at']}")
    if ctx["meta"].get("fell_back"):
        st.caption(
            f"_Requested {ctx['meta'].get('requested_mode', 'LLM Enhanced Mode')}; "
            "fell back to Template Engine Mode (no API key configured)._"
        )

    render_scorecards(ctx)

    if allow_save:
        if st.button("💾 Save Analysis", type="primary"):
            new_id = db.save_analysis(ctx)
            st.success(f"Analysis saved (ID {new_id}). View it in the Saved Analyses tab.")

    st.divider()

    render_score_transparency(ctx)

    # Waste score breakdown chart.
    breakdown = ctx["waste"]["breakdown"]
    non_zero = {k: v for k, v in breakdown.items() if v > 0}
    if non_zero:
        st.markdown("#### Waste Score Contributors")
        chart_df = pd.DataFrame(
            {"Points": list(non_zero.values())}, index=list(non_zero.keys())
        )
        st.bar_chart(chart_df)

    st.divider()

    # The 18 sections in expanders.
    st.markdown("#### Full Workflow Improvement Package")
    for i, title in enumerate(SECTION_ORDER, start=1):
        expanded = i <= 2  # Expand the first couple by default.
        with st.expander(f"{i}. {title}", expanded=expanded):
            st.markdown(ctx["sections"].get(title, "_Not generated._"))

    st.divider()
    render_exports(ctx)


def render_exports(ctx: dict) -> None:
    """Render download buttons for Markdown and CSV exports."""
    st.markdown("#### Exports")
    slug = slugify(ctx["workflow"].get("workflow_name") or "workflow")
    stamp = file_timestamp()

    md = exporters.to_markdown(ctx)
    findings_csv = exporters.dataframe_to_csv(exporters.findings_dataframe(ctx))
    actions_csv = exporters.dataframe_to_csv(exporters.action_plan_dataframe(ctx))
    checklist_csv = exporters.dataframe_to_csv(exporters.checklist_dataframe(ctx))
    future_csv = exporters.dataframe_to_csv(exporters.future_state_dataframe(ctx))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "⬇️ Full Analysis (Markdown)",
            data=md,
            file_name=f"{slug}-{stamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Waste Findings (CSV)",
            data=findings_csv,
            file_name=f"{slug}-findings-{stamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Action Plan (CSV)",
            data=actions_csv,
            file_name=f"{slug}-action-plan-{stamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Standard Work Checklist (CSV)",
            data=checklist_csv,
            file_name=f"{slug}-checklist-{stamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c3:
        st.download_button(
            "⬇️ Future-State Recommendations (CSV)",
            data=future_csv,
            file_name=f"{slug}-future-state-{stamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🧭 Workflow Waste Detector")
    st.caption("Diagnose workflow waste before you automate.")

    st.markdown("**Generation Mode**")
    st.radio(
        "Mode",
        options=[config.MODE_TEMPLATE, config.MODE_LLM],
        index=0,
        help="Template Engine Mode runs fully locally with no API key. "
             "LLM Enhanced Mode uses Google Gemini when an API key is set "
             "(LLM_API_KEY / GEMINI_API_KEY / GOOGLE_API_KEY).",
        label_visibility="collapsed",
        key="generation_mode",
    )

    # Resolve the effective mode (falls back to Template Engine Mode if the
    # LLM key is not configured) and show a clear status indicator.
    requested_mode = st.session_state.get("generation_mode", config.MODE_TEMPLATE)
    effective_mode, fell_back = config.resolve_mode(requested_mode)
    st.caption(f"**Generation Mode:** {effective_mode}")
    if fell_back:
        st.warning(
            "LLM Enhanced Mode is not configured. "
            "The app will use Template Engine Mode instead."
        )
    elif effective_mode == config.MODE_LLM:
        st.info(
            f"LLM Enhanced Mode is configured (Google Gemini · "
            f"{config.get_llm_model_name()}). Analyses will use the Gemini API."
        )

    st.divider()
    st.markdown("**Load a sample workflow**")
    for i, sample in enumerate(SAMPLE_WORKFLOWS):
        if st.button(sample["workflow_name"], key=f"sample_{i}", use_container_width=True):
            load_sample(sample)
            st.rerun()

    st.divider()
    if st.button("🧹 Clear form", use_container_width=True):
        clear_form()
        st.rerun()


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
st.title("AI Workflow Waste Detector")
st.caption(
    "Analyze a workflow, identify Lean waste, score health and automation "
    "readiness, and generate a cleaner future-state design."
)
# Visible generation-mode status (uses the effective mode resolved in the sidebar).
st.markdown(f"**Generation Mode:** `{effective_mode}`")

tab_input, tab_analysis, tab_saved, tab_dashboard = st.tabs(
    ["📝 Input", "📊 Generated Analysis", "🗂️ Saved Analyses", "📈 Dashboard"]
)

# ---- Input tab ----
with tab_input:
    st.markdown("### Describe the workflow")
    st.caption(
        "Fill in what you know. For list-style fields, enter one item per line. "
        "Required: workflow name, description, and steps."
    )

    left, right = st.columns(2)
    half = (len(FIELD_DEFS) + 1) // 2
    for idx, (key, label, is_list, placeholder) in enumerate(FIELD_DEFS):
        target = left if idx < half else right
        display_label = f"{label} *" if key in REQUIRED_FIELDS else label
        with target:
            if is_list:
                st.text_area(display_label, key=key, placeholder=placeholder, height=110)
            elif key in ("current_description", "workflow_purpose",
                         "future_state_outcome", "additional_notes"):
                st.text_area(display_label, key=key, placeholder=placeholder, height=90)
            else:
                st.text_input(display_label, key=key, placeholder=placeholder)

    st.divider()
    generate = st.button("⚙️ Generate Workflow Analysis", type="primary")
    st.caption("Required fields are marked with * in their labels above.")

    if generate:
        wf = collect_form_values()
        result = validate_inputs(wf)

        if not result["ok"]:
            st.error("Please fix the following before generating:")
            for error in result["errors"]:
                st.error(f"• {error}")
            if result["warnings"]:
                with st.expander("Optional suggestions to improve the analysis"):
                    for warning in result["warnings"]:
                        st.write(f"- {warning}")
        else:
            requested = st.session_state.get("generation_mode", config.MODE_TEMPLATE)
            # The app calls the provider interface, not template functions directly.
            ctx = providers.generate(requested, wf)
            st.session_state["analysis"] = ctx

            if ctx["meta"].get("fell_back"):
                st.warning(
                    "LLM Enhanced Mode is not configured. "
                    "The app used Template Engine Mode instead."
                )
            st.success(
                f"✅ Analysis generated using **{ctx['meta']['mode']}**. "
                "Open the **Generated Analysis** tab to review it."
            )
            if result["warnings"]:
                with st.expander("Optional suggestions to make the analysis even stronger"):
                    for warning in result["warnings"]:
                        st.write(f"- {warning}")

# ---- Generated Analysis tab ----
with tab_analysis:
    if st.session_state["analysis"] is None:
        st.info("No analysis yet. Fill in the Input tab and click Generate Workflow Analysis.")
    else:
        render_analysis(st.session_state["analysis"], allow_save=True)

# ---- Saved Analyses tab ----
with tab_saved:
    st.markdown("### Saved Analyses")
    saved = db.list_analyses()
    if not saved:
        st.info("No saved analyses yet. Generate one and click Save Analysis.")
    else:
        table_df = pd.DataFrame(saved)[
            [
                "id", "workflow_name", "workflow_owner", "team_function",
                "waste_score", "automation_score", "priority", "created_at",
            ]
        ].rename(
            columns={
                "id": "ID",
                "workflow_name": "Workflow",
                "workflow_owner": "Owner",
                "team_function": "Team",
                "waste_score": "Waste",
                "automation_score": "Automation",
                "priority": "Priority",
                "created_at": "Created",
            }
        )
        st.dataframe(table_df, use_container_width=True, hide_index=True)

        options = {f"#{r['id']} — {r['workflow_name']}": r["id"] for r in saved}
        choice = st.selectbox("Select an analysis to view", list(options.keys()))
        selected_id = options[choice]

        c1, c2 = st.columns([1, 1])
        with c1:
            view = st.button("👁️ View Analysis", use_container_width=True)
        with c2:
            if st.button("🗑️ Delete Analysis", use_container_width=True):
                db.delete_analysis(selected_id)
                st.success(f"Deleted analysis #{selected_id}.")
                st.rerun()

        if view:
            ctx = db.get_analysis(selected_id)
            if ctx:
                st.divider()
                render_analysis(ctx, allow_save=False)

# ---- Dashboard tab ----
with tab_dashboard:
    st.markdown("### Dashboard")
    metrics = db.dashboard_metrics()

    if metrics["total"] == 0:
        st.info("No data yet. Save at least one analysis to populate the dashboard.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Saved Workflows", metrics["total"])
        m2.metric("Average Waste Score", metrics["avg_waste"])
        m3.metric("Average Automation Readiness", metrics["avg_automation"])

        m4, m5 = st.columns(2)
        m4.metric("High-Waste Workflows", metrics["high_waste_count"])
        m5.metric("Workflows Ready for Automation", metrics["ready_count"])

        st.divider()
        st.markdown("#### Waste Findings by Category")
        by_cat = metrics["findings_by_category"]
        if by_cat:
            cat_df = pd.DataFrame(
                {"Count": list(by_cat.values())}, index=list(by_cat.keys())
            ).sort_values("Count", ascending=False)
            st.bar_chart(cat_df)
        else:
            st.caption("No waste findings recorded yet.")
