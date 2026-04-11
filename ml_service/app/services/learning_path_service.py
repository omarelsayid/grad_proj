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

REQUIRED_FEATURES = [
    "gap", "importance_weight", "complexity_level", "dag_edge_weight",
    "duration_hours", "resource_skill_level", "employee_avg_score", "employee_courses_done",
]
SKILL_LEVEL_MAP = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}


def _load() -> None:
    global _model, _model_loaded
    _model_loaded = True
    model_path = Path(settings.MODEL_DIR) / "learning_path_model.pkl"
    if model_path.exists():
        _model = joblib.load(model_path)


def recommend_learning_path(req: LearningPathRequest) -> LearningPathResponse:
    global _model, _model_loaded
    if not _model_loaded:
        _load()

    # Group resources by skill
    resources_by_skill: dict[str, list] = {}
    for res in req.available_resources:
        resources_by_skill.setdefault(res.skill_id, []).append(res)

    # Sort skills by importance descending (highest priority first)
    sorted_skills = sorted(req.missing_skills, key=lambda s: -s.importance_weight)
    ordered_skill_ids = [s.skill_id for s in sorted_skills]

    recommendations: list[RecommendedItem] = []
    total_hours = 0.0

    for skill in sorted_skills:
        skill_resources = resources_by_skill.get(skill.skill_id, [])
        if not skill_resources:
            continue

        if _model is not None:
            # Score resources with the GBDT model
            results: list[tuple] = []
            for res in skill_resources:
                features = pd.DataFrame([{
                    "gap":                   skill.gap,
                    "importance_weight":     skill.importance_weight,
                    "complexity_level":      skill.complexity_level,
                    "dag_edge_weight":       0.5,   # unknown at inference time
                    "duration_hours":        res.duration_hours,
                    "resource_skill_level":  SKILL_LEVEL_MAP.get(res.skill_level, 2),
                    "employee_avg_score":    req.employee_avg_score,
                    "employee_courses_done": req.employee_courses_done,
                }])[REQUIRED_FEATURES]
                pred_score = float(_model.predict(features)[0])
                results.append((res, pred_score))

            results.sort(key=lambda x: x[1], reverse=True)
            best_res, best_score = results[0]
        else:
            # Fallback: pick shortest resource matching skill level heuristically
            best_res   = min(skill_resources, key=lambda r: abs(
                SKILL_LEVEL_MAP.get(r.skill_level, 2) - int(skill.complexity_level)
            ))
            best_score = 50.0   # unknown

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
