"""
Learning Path Service — Model 4 (Fixed)

The trained model (learning_path_model.pkl) is an LGBMRegressor trained with
a leave-one-out emp_avg_score feature (no target leakage).

Feature alignment note
----------------------
The training script (train_learning_path_model.py) uses an extended feature
set that may include employee-core columns when employees_core.csv is present.
The SERVICE_FEATURES list below is the guaranteed-available subset that this
endpoint can populate from the LearningPathRequest alone.  If a
learning_path_features.pkl is present alongside the model, it is loaded and
used so that the service automatically mirrors whatever the training script
produced — missing columns are zero-filled.
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from app.config import settings
from app.schemas.learning_path import (
    LearningPathRequest,
    LearningPathResponse,
    RecommendedItem,
)

_model = None
_model_loaded = False
_feature_names: list[str] = []

# Baseline feature set — always available from the API request
SERVICE_FEATURES = [
    "emp_proficiency",
    "resource_skill_level",
    "skill_gap_proxy",
    "complexity_level",
    "dag_edge_weight",
    "duration_hours",
    "emp_avg_score",
    "emp_courses_done",
    "attempt_number",
]

SKILL_LEVEL_MAP = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}


def _load() -> None:
    global _model, _model_loaded, _feature_names
    _model_loaded = True
    model_dir  = Path(settings.MODEL_DIR)
    model_path = model_dir / "learning_path_model.pkl"
    feat_path  = model_dir / "learning_path_features.pkl"

    if model_path.exists():
        _model = joblib.load(model_path)

    # Use saved feature list if available; fall back to SERVICE_FEATURES
    if feat_path.exists():
        try:
            _feature_names = joblib.load(feat_path)
        except Exception:
            _feature_names = list(SERVICE_FEATURES)
    else:
        _feature_names = list(SERVICE_FEATURES)


def recommend_learning_path(req: LearningPathRequest) -> LearningPathResponse:
    global _model, _model_loaded
    if not _model_loaded:
        _load()

    # Index resources by skill_id
    resources_by_skill: dict[str, list] = {}
    for res in req.available_resources:
        resources_by_skill.setdefault(res.skill_id, []).append(res)

    # Sort skills by importance descending (most critical first)
    sorted_skills = sorted(req.missing_skills, key=lambda s: -s.importance_weight)
    ordered_skill_ids = [s.skill_id for s in sorted_skills]

    recommendations: list[RecommendedItem] = []
    total_hours = 0.0

    for skill in sorted_skills:
        skill_resources = resources_by_skill.get(skill.skill_id, [])
        if not skill_resources:
            continue

        if _model is not None:
            results: list[tuple] = []
            for res in skill_resources:
                res_level = SKILL_LEVEL_MAP.get(res.skill_level, 2)
                gap_proxy = max(res_level - skill.gap, 0)

                base_row = {
                    "emp_proficiency":    max(0.0, float(skill.gap) - float(skill.gap)),  # infer as 0
                    "resource_skill_level": res_level,
                    "skill_gap_proxy":    gap_proxy,
                    "complexity_level":   skill.complexity_level,
                    "dag_edge_weight":    0.5,           # unknown at inference; use neutral prior
                    "duration_hours":     res.duration_hours,
                    "emp_avg_score":      req.employee_avg_score,
                    "emp_courses_done":   req.employee_courses_done,
                    "attempt_number":     1,
                }

                # Build full feature row; zero-fill any extra columns the model
                # was trained with (e.g. age, tenure_years from employees_core)
                feat_row = {col: base_row.get(col, 0.0) for col in _feature_names}
                features = pd.DataFrame([feat_row])[_feature_names]

                pred_score = float(_model.predict(features)[0])
                results.append((res, pred_score))

            results.sort(key=lambda x: x[1], reverse=True)
            best_res, best_score = results[0]
        else:
            # Fallback: pick resource closest to skill complexity level
            best_res   = min(skill_resources, key=lambda r: abs(
                SKILL_LEVEL_MAP.get(r.skill_level, 2) - int(skill.complexity_level)
            ))
            best_score = 50.0

        if skill.importance_weight >= 0.7:
            priority = "high"
        elif skill.importance_weight >= 0.4:
            priority = "medium"
        else:
            priority = "low"

        recommendations.append(RecommendedItem(
            skill_id=skill.skill_id,
            resource_id=best_res.resource_id,
            resource_title=best_res.title,
            predicted_completion_score=round(best_score, 2),
            priority=priority,
        ))
        total_hours += best_res.duration_hours

    return LearningPathResponse(
        employee_id=req.employee_id,
        job_role_id=req.job_role_id,
        ordered_skills=ordered_skill_ids,
        recommendations=recommendations,
        estimated_completion_hours=round(total_hours, 1),
    )
