"""SQLite storage for saved workflow analyses and dashboard metrics."""

from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter

# Database lives in the local data/ folder next to the project root.
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(_DATA_DIR, "workflow_waste.db")


def _get_connection() -> sqlite3.Connection:
    """Open a SQLite connection, creating the data directory if needed."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the analyses table if it does not already exist."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_name TEXT,
                workflow_owner TEXT,
                team_function TEXT,
                waste_score INTEGER,
                waste_status TEXT,
                automation_score INTEGER,
                automation_status TEXT,
                priority TEXT,
                simplify_first INTEGER,
                top_categories TEXT,
                created_at TEXT,
                payload TEXT
            )
            """
        )
        conn.commit()


def save_analysis(ctx: dict) -> int:
    """Persist a generated analysis. Returns the new row id."""
    wf = ctx["workflow"]
    categories = sorted({f["category"] for f in ctx.get("waste_findings", [])})

    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses (
                workflow_name, workflow_owner, team_function,
                waste_score, waste_status, automation_score, automation_status,
                priority, simplify_first, top_categories, created_at, payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                wf.get("workflow_name") or "Unnamed Workflow",
                wf.get("workflow_owner") or "",
                wf.get("team_function") or "",
                ctx["waste"]["score"],
                ctx["waste"]["status"],
                ctx["automation"]["score"],
                ctx["automation"]["status"],
                ctx["priority"][0],
                1 if ctx["simplify_first"] else 0,
                ", ".join(categories),
                ctx["meta"]["generated_at"],
                json.dumps(ctx),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_analyses() -> list[dict]:
    """Return summary rows for all saved analyses, newest first."""
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, workflow_name, workflow_owner, team_function,
                   waste_score, waste_status, automation_score, automation_status,
                   priority, simplify_first, top_categories, created_at
            FROM analyses
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_analysis(analysis_id: int) -> dict | None:
    """Return the full analysis context for a saved analysis, or None."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT payload FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
    if not row:
        return None
    return json.loads(row["payload"])


def delete_analysis(analysis_id: int) -> None:
    """Delete a saved analysis by id."""
    with _get_connection() as conn:
        conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()


def dashboard_metrics() -> dict:
    """Compute aggregate metrics across all saved analyses for the dashboard."""
    rows = list_analyses()
    total = len(rows)

    if total == 0:
        return {
            "total": 0,
            "avg_waste": 0,
            "avg_automation": 0,
            "high_waste_count": 0,
            "ready_count": 0,
            "findings_by_category": {},
        }

    avg_waste = round(sum(r["waste_score"] for r in rows) / total, 1)
    avg_automation = round(sum(r["automation_score"] for r in rows) / total, 1)
    high_waste = sum(1 for r in rows if r["waste_score"] >= 61)
    ready = sum(1 for r in rows if r["automation_score"] >= 80)

    # Aggregate waste findings by category across every saved analysis.
    counter: Counter[str] = Counter()
    with _get_connection() as conn:
        payloads = conn.execute("SELECT payload FROM analyses").fetchall()
    for row in payloads:
        ctx = json.loads(row["payload"])
        for finding in ctx.get("waste_findings", []):
            counter[finding["category"]] += 1

    return {
        "total": total,
        "avg_waste": avg_waste,
        "avg_automation": avg_automation,
        "high_waste_count": high_waste,
        "ready_count": ready,
        "findings_by_category": dict(counter),
    }
