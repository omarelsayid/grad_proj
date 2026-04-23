"""
Skill Gaps Service — Model 3 (aligned with notebook compute_realistic_gaps)

Criticality tiers match the notebook's pct_employees_meeting thresholds:

  pct_employees_meeting  | criticality
  -----------------------|------------
  < 10 %                 | critical    (fewer than 1-in-10 employees meeting the bar)
  < 25 %                 | high
  < 50 %                 | medium
  < 75 %                 | low
  >= 75 %                | surplus     (most employees already meet the requirement)

Live DB path: queries PostgreSQL for current headcount and proficiency data.
Fallback path: loads the precomputed real_skill_gap_analysis.pkl produced by
               the notebook's Model 3 cell.  If neither is available an empty
               response is returned.
"""

from __future__ import annotations

import joblib
from pathlib import Path

from app.config import settings
from app.schemas.skill_gaps import DepartmentGapSummary, SkillGapEntry, SkillGapsResponse

# ── Criticality: based on % employees meeting proficiency requirement ─────────
# Aligns with notebook compute_realistic_gaps() tiers
def _get_criticality(pct_meeting: float) -> str:
    """
    pct_meeting — fraction (0–1) of employees currently meeting the
    proficiency requirement for this skill.
    """
    if pct_meeting < 0.10:
        return "critical"
    if pct_meeting < 0.25:
        return "high"
    if pct_meeting < 0.50:
        return "medium"
    if pct_meeting < 0.75:
        return "low"
    return "surplus"


# Legacy helper kept for the DB path which uses demand/supply ratio
def _get_criticality_from_ratio(ratio: float) -> str:
    """
    ratio = demand / supply.  High ratio → more demand than supply → critical.
    Converts ratio to an approximate pct_meeting and delegates to the main fn.
    """
    # ratio > 4 → ~< 25% meeting  → high/critical
    # ratio > 2 → ~< 50% meeting  → medium/high
    if ratio >= 4.0:
        return "critical"
    if ratio >= 2.0:
        return "high"
    if ratio >= 1.2:
        return "medium"
    return "low"


def _load_baseline():
    """Load precomputed real_skill_gap_analysis.pkl (Model 3 notebook output)."""
    for name in ("real_skill_gap_analysis.pkl", "skill_gap_baseline.pkl"):
        path = Path(settings.MODEL_DIR) / name
        if path.exists():
            return joblib.load(path), name
    return None, None


def _from_db() -> SkillGapsResponse:
    """Compute live skill gaps from PostgreSQL using pct_employees_meeting."""
    from app.db.connection import get_db

    with get_db() as conn:
        cur = conn.cursor()

        # Required skills + headcount per role
        cur.execute("""
            SELECT
                jrr.skill_id            AS skill_id,
                jr.title                AS department,
                jrr.min_proficiency,
                jrr.importance_weight,
                COUNT(e.id)             AS headcount
            FROM job_roles             jr
            JOIN role_required_skills  jrr ON jr.id = jrr.role_id
            JOIN employees             e   ON e.current_role = jr.title
            GROUP BY jrr.skill_id, jr.title,
                     jrr.min_proficiency, jrr.importance_weight
        """)
        demand_rows = cur.fetchall()

        # Per-skill employee proficiency distribution
        cur.execute("""
            SELECT skill_id,
                   AVG(proficiency)   AS avg_proficiency,
                   COUNT(employee_id) AS employee_count
            FROM employee_skills
            GROUP BY skill_id
        """)
        supply_rows = cur.fetchall()

        cur.execute("SELECT id AS skill_id, name AS skill_name FROM skills")
        skill_names = {row[0]: row[1] for row in cur.fetchall()}

    supply_map: dict[str, tuple[float, int]] = {
        row[0]: (float(row[1]), int(row[2])) for row in supply_rows
    }

    # Aggregate demand and dept mapping
    demand_map: dict[str, dict] = {}
    dept_map:   dict[str, list[str]] = {}

    for skill_id, dept, min_prof, importance, headcount in demand_rows:
        if skill_id not in demand_map:
            demand_map[skill_id] = {
                "total_demand": 0.0,
                "total_headcount": 0,
                "min_proficiency": min_prof,
            }
        demand_map[skill_id]["total_demand"]    += min_prof * importance * headcount
        demand_map[skill_id]["total_headcount"] += headcount
        dept_map.setdefault(skill_id, [])
        if dept not in dept_map[skill_id]:
            dept_map[skill_id].append(dept)

    entries: list[SkillGapEntry] = []
    for skill_id, d in demand_map.items():
        avg_prof, emp_count = supply_map.get(skill_id, (0.0, 0))
        min_req             = d["min_proficiency"]
        supply_score        = avg_prof * emp_count
        demand_score        = d["total_demand"]
        ratio               = min(demand_score / (supply_score + 1e-8), 10.0)

        # Estimate pct_meeting from avg proficiency vs min_proficiency
        pct_meeting = float(avg_prof / min_req) if min_req > 0 else 1.0
        pct_meeting = max(0.0, min(1.0, pct_meeting))

        entries.append(SkillGapEntry(
            skill_id=skill_id,
            skill_name=skill_names.get(skill_id),
            demand_score=round(demand_score, 2),
            supply_score=round(supply_score, 2),
            gap_ratio=round(ratio, 3),
            criticality=_get_criticality(pct_meeting),
            departments_affected=dept_map.get(skill_id, []),
        ))

    entries.sort(key=lambda e: e.gap_ratio, reverse=True)

    dept_entries: dict[str, list[SkillGapEntry]] = {}
    for e in entries:
        for dept in e.departments_affected:
            dept_entries.setdefault(dept, []).append(e)

    dept_summaries = [
        DepartmentGapSummary(
            department=dept,
            top_gaps=sorted(gaps, key=lambda x: x.gap_ratio, reverse=True)[:5],
            overall_gap_score=round(sum(g.gap_ratio for g in gaps) / len(gaps), 3),
        )
        for dept, gaps in dept_entries.items()
    ]

    return SkillGapsResponse(
        total_skills_analyzed=len(entries),
        critical_skills=sum(1 for e in entries if e.criticality == "critical"),
        skill_gaps=entries,
        department_summaries=dept_summaries,
    )


def _from_baseline() -> SkillGapsResponse:
    """
    Serve precomputed results from the notebook Model 3 output.

    Handles two formats:
      real_skill_gap_analysis.pkl  — DataFrame from compute_realistic_gaps()
        columns: skill_id, skill_name, pct_employees_meeting, criticality, ...
      skill_gap_baseline.pkl (legacy) — DataFrame with gap_ratio column
    """
    data, source_name = _load_baseline()
    if data is None:
        return SkillGapsResponse(
            total_skills_analyzed=0,
            critical_skills=0,
            skill_gaps=[],
            department_summaries=[],
        )

    import pandas as pd

    # Normalise to DataFrame
    if not isinstance(data, pd.DataFrame):
        return SkillGapsResponse(
            total_skills_analyzed=0, critical_skills=0,
            skill_gaps=[], department_summaries=[],
        )

    entries: list[SkillGapEntry] = []
    for _, row in data.iterrows():
        skill_id = str(row.get("skill_id", ""))
        if not skill_id:
            continue

        # Use pct_employees_meeting for criticality when available (new format)
        if "pct_employees_meeting" in row.index:
            pct = float(row["pct_employees_meeting"])
            criticality = _get_criticality(pct)
            gap_ratio   = round(1.0 - pct, 3)          # invert for sorting
        elif "criticality" in row.index:
            criticality = str(row["criticality"])
            gap_ratio   = float(row.get("gap_ratio", 0.0))
        else:
            gap_ratio   = float(row.get("gap_ratio", 0.0))
            criticality = _get_criticality_from_ratio(gap_ratio)

        entries.append(SkillGapEntry(
            skill_id=skill_id,
            skill_name=row.get("skill_name") or row.get("skill_name_x"),
            demand_score=float(row.get("total_demand", row.get("demand_score", 0))),
            supply_score=float(row.get("total_supply", row.get("supply_score", 0))),
            gap_ratio=gap_ratio,
            criticality=criticality,
            departments_affected=list(row.get("departments_affected", [])),
        ))

    entries.sort(key=lambda e: e.gap_ratio, reverse=True)

    dept_entries: dict[str, list[SkillGapEntry]] = {}
    for e in entries:
        for dept in e.departments_affected:
            dept_entries.setdefault(dept, []).append(e)

    dept_summaries = [
        DepartmentGapSummary(
            department=dept,
            top_gaps=sorted(gaps, key=lambda x: x.gap_ratio, reverse=True)[:5],
            overall_gap_score=round(sum(g.gap_ratio for g in gaps) / len(gaps), 3),
        )
        for dept, gaps in dept_entries.items()
    ]

    return SkillGapsResponse(
        total_skills_analyzed=len(entries),
        critical_skills=sum(1 for e in entries if e.criticality == "critical"),
        skill_gaps=entries,
        department_summaries=dept_summaries,
    )


def analyze_skill_gaps() -> SkillGapsResponse:
    """Try live DB first; fall back to precomputed notebook baseline."""
    try:
        return _from_db()
    except Exception:
        return _from_baseline()
