# AI Workflow Waste Detector

[![▶ Live Demo](https://img.shields.io/badge/%E2%96%B6_Live_Demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://ai-workflow-waste-detector.streamlit.app/)

**▶️ Try it live:** https://ai-workflow-waste-detector.streamlit.app/

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36%2B-FF4B4B?logo=streamlit&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Last Commit](https://img.shields.io/github/last-commit/Sviless/AI-Workflow-Waste-Detector)
![Code Size](https://img.shields.io/github/languages/code-size/Sviless/AI-Workflow-Waste-Detector)

Diagnose workflow waste **before** you automate it.

AI Workflow Waste Detector is a local-first web application that helps teams analyze business, engineering, operational, and knowledge-work workflows to find waste, bottlenecks, unclear ownership, rework loops, duplicated effort, and automation opportunities. It applies Lean, 5S/6S, and operational-excellence thinking to modern digital workflows and then recommends a cleaner future-state design.

It runs entirely on your machine with **Template Engine Mode** — no API key, no internet, no cloud dependency.

---

## 1. Project Overview

Teams often try to automate a broken workflow before simplifying it, which just makes waste run faster. This tool flips that order: it first **diagnoses** where the waste is, scores the workflow's health and automation readiness, and only then recommends automation — and only when the process is stable enough to benefit.

You describe a workflow through a structured form, click **Generate**, and receive an 18-section workflow improvement package with scores, Lean waste findings, a 5S/6S assessment, a future-state design, a standard work checklist, an action plan, and exportable reports.

## 2. Problem This Tool Solves

- Waste hides inside "the way we've always done it."
- Duplicate trackers, redundant approvals, and status meetings quietly consume capacity.
- Unclear ownership creates single points of failure and slow decisions.
- Teams automate first and simplify never, locking in the waste.

This tool makes the waste visible, categorizes it with a shared Lean vocabulary, and gives a concrete path to a leaner future state.

## 3. Why Workflow Waste Matters

Every unnecessary handoff, approval, wait, and duplicate report adds cycle time, cost, and risk. In knowledge work this waste is often invisible because it lives in email threads, spreadsheets, and meetings rather than on a factory floor. Naming and scoring the waste is the first step to removing it — and to knowing whether a workflow is even a good candidate for automation.

## 4. Key Features

- **Structured input form** capturing 20 aspects of a workflow.
- **Template Engine Mode** generation — fully local, rule-based analysis.
- **Workflow Waste Score (0–100)** with health status.
- **Automation Readiness Score (0–100)** with readiness status.
- **"Simplify before automating" guardrail** when waste is high but readiness is low.
- **18-section improvement package** (executive summary through final summary).
- **Lean waste analysis** across 10 categories.
- **5S/6S digital workflow assessment** (Sort, Set in Order, Shine, Standardize, Sustain, Safety).
- **Recommended future-state workflow** and **standard work checklist**.
- **Improvement action plan** with quick wins and longer-term items.
- **Save, view, and delete analyses** in local SQLite storage.
- **Dashboard** with aggregate metrics and waste-by-category charts.
- **Exports:** full Markdown report plus CSVs for findings, action plan, checklist, and future-state recommendations.

## 5. Technology Stack

- **Python**
- **Streamlit** — user interface
- **SQLite** — local storage
- **pandas** — data handling and CSV export
- **Streamlit built-in charts** — visualizations

No external APIs. No secrets. No internet required.

## 6. Folder Structure

```
ai-workflow-waste-detector/
├── app.py                 # Streamlit UI: form, tabs, analysis display, dashboard
├── requirements.txt       # Dependencies (streamlit, pandas)
├── README.md              # This file
├── .env.example           # Sample env config for LLM Enhanced Mode (no real key)
├── .gitignore             # Ignores .env, local db, and exports
├── data/
│   └── workflow_waste.db  # SQLite database (created at runtime)
├── outputs/               # Optional location for exported reports
└── src/
    ├── __init__.py
    ├── config.py          # Reads env vars; resolves generation mode (no key exposed)
    ├── template_engine.py # Template Engine Mode generation logic
    ├── db.py              # SQLite create/save/retrieve/metrics
    ├── exporters.py       # Markdown + CSV exports
    ├── scoring.py         # Waste and automation readiness scoring
    ├── validators.py      # Input validation and quality warnings
    ├── sample_data.py     # Generic sample workflows + field definitions
    ├── utils.py           # Text cleanup, list parsing, formatting helpers
    └── providers/         # Pluggable generation providers
        ├── __init__.py        # Provider factory (get_provider / generate)
        ├── base_provider.py   # Abstract provider interface
        ├── template_provider.py  # Wraps Template Engine Mode (default)
        └── llm_provider.py    # LLM Enhanced Mode (future-ready, falls back)
```

## 7. Setup Instructions

Requires Python 3.10 or newer.

```powershell
# From the project folder
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS/Linux use `source .venv/bin/activate` instead.

## 8. How to Run the App

```powershell
streamlit run app.py
```

Streamlit opens the app in your browser (usually http://localhost:8501).

## Generation Modes

The app uses a pluggable **provider architecture**. The UI calls a provider
interface, not the template functions directly, so generation is swappable.

### Template Engine Mode (default)

- Local-first — runs entirely on your machine.
- No API key required.
- Uses built-in Lean/6S rules, scoring logic, and templates.
- Produces all 18 analysis sections.
- Portfolio-safe.

To run in Template Engine Mode (the default):

```powershell
streamlit run app.py
```

### LLM Enhanced Mode (future-ready)

- Future-ready architecture behind the same provider interface.
- Reads an `LLM_API_KEY` environment variable — never hardcoded.
- Provider-neutral: can later connect to OpenAI, Azure OpenAI, Claude, or another LLM.
- **Not required** for the app to run. If no key is set, the app automatically
  falls back to Template Engine Mode and shows:
  *"LLM Enhanced Mode is not configured. The app will use Template Engine Mode instead."*

To prepare for LLM Enhanced Mode, create a `.env` file (or set an environment
variable):

```
LLM_API_KEY=your_key_here
```

You can copy `.env.example` to `.env` as a starting point. The actual network
call lives in a single, clearly marked function (`_call_llm`) in
[src/providers/llm_provider.py](src/providers/llm_provider.py); until it is
implemented the app keeps using Template Engine Mode.

> **Important:** Do not include a real key in the repo, and do not commit `.env`
> files. `.env` is already listed in `.gitignore`.

## 9. Example Use Case

A program manager runs a **Weekly Status Reporting** workflow. Contributors update personal spreadsheets, a manager reconciles conflicting numbers by hand, and a slide deck is rebuilt each week before a leadership review.

Using the app (load the built-in sample of the same name), the tool:

- Flags **duplicate trackers**, **rework/reconciliation**, **excess handoffs**, and **meeting waste**.
- Returns a **high waste score** and a **low-to-moderate automation readiness score**.
- Displays the guardrail: *"Do not automate this workflow yet. Simplify, standardize, and clarify ownership first."*
- Recommends a **single source of truth**, **clear field ownership**, and **auto-generated reporting** as the future state.

The manager exports the Markdown package and the action-plan CSV to drive an improvement effort.

## 10. Portfolio Value

This project demonstrates the ability to connect **operational excellence** with **software engineering**: modeling a real business problem, encoding Lean/6S expertise into rules and scoring, and delivering a clean, modular, runnable application with persistence, exports, and a dashboard. It is portfolio-safe — it uses only generic sample data and contains no confidential or company-specific information.

## 11. Possible Future Enhancements

- **LLM Enhanced Mode** (the architecture already routes generation through a single interface).
- CSV or Excel workflow import.
- Process map visualization.
- Swimlane diagram generation.
- Document upload.
- RAG-based workflow evidence review.
- Source attribution.
- Multi-user support.
- Cloud deployment.

## 12. Resume Bullets

- Built a local-first AI Workflow Waste Detector using Python, Streamlit, SQLite, and Lean/6S principles to identify bottlenecks, rework loops, duplicated reporting, unclear ownership, and automation readiness risks in operational workflows.
- Developed a template-driven workflow improvement application that maps digital process waste to Lean categories, scores workflow health, and generates future-state recommendations, standard work checklists, and action plans.
- Designed a portfolio-safe AI-assisted operational excellence tool with Template Engine Mode, structured exports, dashboard metrics, and future-ready architecture for LLM-enhanced workflow analysis.
- Built an AI Workflow Waste Detector with local Template Engine Mode and LLM-ready provider architecture to identify process waste, automation readiness risks, Lean/6S improvement opportunities, and future-state workflow recommendations.

---

## How Template Engine Mode Works

Template Engine Mode generates the entire analysis locally using Python rules and templates — no external model or API. It:

1. Parses each input field (list fields are split into discrete items).
2. Computes signals such as counts of steps, handoffs, approvals, waiting points, duplicate trackers, meetings, tools, plus rework and risk indicators from keywords.
3. Scores the workflow (waste and automation readiness).
4. Generates structured findings, a 5S/6S assessment, a future-state design, a standard work checklist, and an action plan.
5. Renders 18 Markdown sections from that structured data.

All generation flows through a single `generate_analysis()` function, so a future **LLM Enhanced Mode** can implement the same interface without changing the UI, storage, or exports.

## How the Workflow Waste Score Is Calculated

The waste score (0–100, higher = more waste) sums weighted, capped contributions from:

- Number of process steps
- Number of handoffs
- Number of approvals
- Number of waiting points
- Number of duplicate trackers/reports
- Number of meetings
- Rework indicators (list items + keywords)
- Tool complexity
- Risk level
- Ownership clarity (penalty if no owner)
- Documentation clarity (penalty if thin)

Status bands:

- **0–30:** Low Waste / Healthy Workflow
- **31–60:** Moderate Waste / Improvement Recommended
- **61–100:** High Waste / Redesign Recommended

## How Automation Readiness Is Calculated

The automation readiness score (0–100, higher = more ready) awards points for ten readiness checks:

- Clear inputs
- Clear outputs
- Stable process steps
- Defined owner
- Defined trigger
- Defined success criteria
- Low ambiguity
- Low exception rate
- Clear data source
- Standardized tracker or form

A small penalty is applied for high risk. Status bands:

- **80–100:** Ready for Automation
- **50–79:** Simplify Before Automating
- **0–49:** Not Ready for Automation

When waste is high but readiness is low, the app explicitly advises:
**"Do not automate this workflow yet. Simplify, standardize, and clarify ownership first."**

## How to Describe This Project on a Resume

Use any of the resume bullets in Section 12 above. In short: a Python/Streamlit/SQLite operational-excellence tool that applies Lean and 5S/6S to diagnose workflow waste, scores workflow health and automation readiness, and generates future-state recommendations, checklists, and action plans — with exports and a dashboard, built portfolio-safe and ready to extend with an LLM-enhanced mode.
