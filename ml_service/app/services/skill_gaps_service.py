"""
Skill Gaps Service — queries PostgreSQL live for current org data,
falls back to precomputed baseline (skill_gap_baseline.pkl) if DB is unavailable.
"""

from __future__ import annotations

import joblib
from pathlib import Path

from app.config import settings
from app.schemas.skill_gaps import DepartmentGapSummary, SkillGapEntry, SkillGapsResponse

_CRITICALITY = {
    2.0: "critical",   # supply covers < 50 % of demand
    1.5: "high",       # supply covers < 67 %
    1.2: "medium",     # supply covers < 83 %
    0.0: "low",
}


def _get_criticality(ratio: float) -> str:
    for threshold, label in _CRITICALITY.items():
        if ratio >= threshold:
            return label
    return "low"


def _load_baseline():
    path = Path(settings.MODEL_DIR) / "skill_gap_baseline.pkl"
    if not path.exists():
        return None
    return joblib.load(path)


def _from_db() -> SkillGapsResponse:
    """Compute live skill gaps from PostgreSQL."""
    from app.db.connection import get_db

    with get_db() as conn:
        cur = conn.cursor()

        # --- Demand side: role requirements weighted by headcount ---
        cur.execute("""
            SELECT
                jrr.required_skill_id   AS skill_id,
                jr.title                AS department,
                jrr.min_proficiency,
                jrr.importance_weight,
                COUNT(p.user_id)        AS headcount
            FROM job_roles            jr
            JOIN job_role_requirements jrr ON jr.id = jrr.job_role_id
            JOIN profiles              p   ON p.position = jr.title
            GROUP BY jrr.required_skill_id, jr.title,
                     jrr.min_proficiency, jrr.importance_weight
        """)
        demand_rows = cur.fetchall()

        # --- Supply side: average proficiency per skill across all employees ---
        cur.execute("""
            SELECT skill_id,
                   AVG(proficiency)   AS avg_proficiency,
                   COUNT(employee_id) AS employee_count
            FROM employee_skills
            GROUP BY skill_id
        """)
        supply_rows = cur.fetchall()

        # --- Optional: skill names ---
        cur.execute("SELECT skill_id, skill_name FROM skills_catalog")
        skill_names = {row[0]: row[1] for row in cur.fetchall()}

    supply_map: dict[str, tuple[float, int]] = {
        row[0]: (float(row[1]), int(row[2])) for row in supply_rows
    }

    demand_map:   dict[str, float] = {}
    dept_map:     dict[str, list[str]] = {}

    for skill_id, dept, min_prof, importance, headcount in demand_rows:
        wt = min_prof * importance * headcount
        demand_map[skill_id] = demand_map.get(skill_id, 0.0) + wt
        dept_map.setdefault(skill_id, [])
        if dept not in dept_map[skill_id]:
            dept_map[skill_id].append(dept)

    entries: list[SkillGapEntry] = []
    for skill_id, demand_score in demand_map.items():
        avg_prof, emp_count = supply_map.get(skill_id, (0.0, 0))
        supply_score = avg_prof * emp_count
        ratio        = min(demand_score / (supply_score + 1e-8), 10.0)

        entries.append(SkillGapEntry(
            skill_id=skill_id,
            skill_name=skill_names.get(skill_id),
            demand_score=round(demand_score, 2),
            supply_score=round(supply_score, 2),
            gap_ratio=round(ratio, 3),
            criticality=_get_criticality(ratio),
            departments_affected=dept_map.get(skill_id, []),
        ))

    entries.sort(key=lambda e: e.gap_ratio, reverse=True)

    # Department summaries
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
    """Serve precomputed baseline when DB is unavailable."""
    df = _load_baseline()
    if df is None:
        return SkillGapsResponse(
            total_skills_analyzed=0,
            critical_skills=0,
            skill_gaps=[],
            department_summaries=[],
        )

    entries: list[SkillGapEntry] = []
    for _, row in df.iterrows():
        entries.append(SkillGapEntry(
            skill_id=str(row["skill_id"]),
            skill_name=row.get("skill_name"),
            demand_score=float(row.get("total_demand", 0)),
            supply_score=float(row.get("total_supply", 0)),
            gap_ratio=float(row.get("gap_ratio", 0)),
            criticality=str(row.get("criticality", "low")),
            departments_affected=row.get("departments_affected", []),
        ))

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
    """Try live DB first; fall back to precomputed baseline."""
    try:
        return _from_db()
    except Exception:
        return _from_baseline()
