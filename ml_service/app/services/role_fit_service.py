"""
Role Fit Service — two-layer approach:
  1. Deterministic algorithmic score (always available, no model needed).
  2. Optional ML refinement using the trained GBR when the model file exists.
     The service falls back gracefully to the algorithmic score if the model
     hasn't been trained yet.
"""

from __future__ import annotations

import numpy as np
import joblib
from pathlib import Path

from app.config import settings
from app.schemas.role_fit import RoleFitRequest, RoleFitResponse, SkillGapDetail

_model = None   # GradientBoostingRegressor or None
_model_loaded = False

FEATURE_COLS = [
    "n_required", "n_matching", "n_missing",
    "coverage_ratio", "weighted_gap", "max_gap", "avg_matched_prof",
]


def _try_load() -> None:
    """Load ML model if available; silently skip if not trained yet."""
    global _model, _model_loaded
    _model_loaded = True
    model_path = Path(settings.MODEL_DIR) / "role_fit_model.pkl"
    if model_path.exists():
        _model = joblib.load(model_path)


def compute_role_fit(req: RoleFitRequest) -> RoleFitResponse:
    global _model, _model_loaded
    if not _model_loaded:
        _try_load()

    emp_skills = {s.skill_id: s.proficiency for s in req.employee_skills}

    matching_skills: list[str] = []
    missing_skills:  list[str] = []
    partial_skills:  list[str] = []
    skill_gaps_detail: list[SkillGapDetail] = []

    total_weighted_gap = 0.0
    total_weight       = 0.0
    matched_profs:  list[float] = []

    for rs in req.role_requirements:
        skill_id   = rs.skill_id
        min_prof   = rs.min_proficiency
        importance = rs.importance_weight
        current    = float(emp_skills.get(skill_id, 0.0))
        gap        = max(min_prof - current, 0.0)

        total_weighted_gap += gap * importance
        # Max gap = min_proficiency (when employee proficiency = 0, the unacquired state)
        total_weight       += min_prof * importance

        if gap == 0:
            status = "met"
            matching_skills.append(skill_id)
            matched_profs.append(current)
        elif current > 0:
            status = "partial"
            partial_skills.append(skill_id)
        else:
            status = "missing"
            missing_skills.append(skill_id)

        skill_gaps_detail.append(SkillGapDetail(
            skill_id=skill_id,
            required=min_prof,
            current=current,
            gap=round(gap, 2),
            importance_weight=importance,
            status=status,
        ))

    # Algorithmic readiness (0–1)
    if total_weight == 0:
        readiness = 1.0
    else:
        readiness = 1.0 - (total_weighted_gap / total_weight)

    # Optional ML refinement
    if _model is not None:
        import pandas as pd
        n_required  = len(req.role_requirements)
        n_matching  = len(matching_skills)
        n_missing   = len(missing_skills)
        features = pd.DataFrame([{
            "n_required":       n_required,
            "n_matching":       n_matching,
            "n_missing":        n_missing,
            "coverage_ratio":   n_matching / n_required if n_required else 0.0,
            "weighted_gap":     (total_weighted_gap / sum(rs.importance_weight for rs in req.role_requirements)) if req.role_requirements else 0.0,
            "max_gap":          max((g.gap for g in skill_gaps_detail), default=0.0),
            "avg_matched_prof": float(np.mean(matched_profs)) if matched_profs else 0.0,
        }])[FEATURE_COLS]
        readiness = float(np.clip(_model.predict(features)[0], 0.0, 1.0))

    fit_score = max(0, min(100, int(readiness * 100)))

    if fit_score >= 85:
        readiness_level = "ready"
    elif fit_score >= 65:
        readiness_level = "near_ready"
    elif fit_score >= 40:
        readiness_level = "needs_development"
    else:
        readiness_level = "not_ready"

    # Sort gaps by importance descending
    skill_gaps_detail.sort(key=lambda x: (-x.importance_weight, -x.gap))

    return RoleFitResponse(
        employee_id=req.employee_id,
        job_role_id=req.job_role_id,
        fit_score=fit_score,
        readiness_level=readiness_level,
        matching_skills=matching_skills,
        missing_skills=missing_skills + partial_skills,
        skill_gaps=skill_gaps_detail,
    )
