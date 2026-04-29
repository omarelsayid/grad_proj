"""
Turnover Prediction Service — Model 1 (Fixed)

The trained model (best_turnover_model.pkl) is an imblearn.Pipeline:
  ImbPipeline([("smote", SMOTE), ("clf", <best classifier>)])

SMOTE only fires during training; at inference the pipeline routes straight
through to the classifier's predict_proba.  The scaler is applied separately
before passing features to the pipeline (matching how training was done).

_top_factors accesses pipe.named_steps["clf"] to reach the underlying
classifier's feature_importances_ or coef_ attribute.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from app.config import settings
from app.schemas.turnover import TurnoverRequest, TurnoverResponse

_model = None           # ImbPipeline (SMOTE + classifier)
_scaler = None          # StandardScaler — applied before the pipeline
_feature_names: list[str] = []

ATTENDANCE_MAP = {"normal": 0, "at_risk": 1, "critical": 2}


def _load() -> None:
    global _model, _scaler, _feature_names
    model_dir = Path(settings.MODEL_DIR)
    _model  = joblib.load(model_dir / "best_turnover_model.pkl")
    _scaler = joblib.load(model_dir / "scaler.pkl")
    try:
        _feature_names = joblib.load(model_dir / "turnover_features.pkl")
    except FileNotFoundError:
        _feature_names = []


def _top_factors(model, feature_names: list[str], n: int = 3) -> list[str]:
    """
    Extract top-n feature names by importance from the pipeline.

    The model may be:
      - An imblearn.Pipeline with a 'clf' step — access clf.feature_importances_
      - A plain sklearn estimator — access model.feature_importances_ directly
    """
    if not feature_names:
        return []

    # Unwrap pipeline to reach the actual classifier
    clf = model
    if hasattr(model, "named_steps"):
        clf = model.named_steps.get("clf", model)

    if hasattr(clf, "feature_importances_"):
        idx = np.argsort(clf.feature_importances_)[::-1][:n]
        return [feature_names[i] for i in idx]

    if hasattr(clf, "coef_"):
        coef = np.abs(clf.coef_[0]) if clf.coef_.ndim > 1 else np.abs(clf.coef_)
        idx = np.argsort(coef)[::-1][:n]
        return [feature_names[i] for i in idx]

    return []


def predict_turnover(req: TurnoverRequest) -> TurnoverResponse:
    global _model, _scaler
    if _model is None:
        _load()

    # Map backend fields → training feature names (must match train_turnover_model.py FEATURE_COLS)
    row = {
        "tenure_years":              req.tenure_days / 365.25,
        "commute_distance_km":       req.commute_distance_km,
        "role_fit_score":            req.role_fit_score,
        "absence_rate":              req.absence_rate,
        "late_rate":                 req.late_arrivals_30d / 30.0,
        "work_life_balance":         req.satisfaction_score / 20.0,  # 0–100 → 0–5 scale
        "attendance_status_encoded": ATTENDANCE_MAP[req.attendance_status],
    }

    # Build DataFrame and align to the saved feature order
    X = pd.DataFrame([row])
    if _feature_names:
        for col in _feature_names:
            if col not in X.columns:
                X[col] = 0
        X = X[_feature_names]

    # Scale first — pass .values (numpy array) to avoid sklearn feature-name warning
    X_scaled = _scaler.transform(X.values)

    # Pipeline routes through SMOTE (no-op at predict time) → classifier
    risk_score = float(_model.predict_proba(X_scaled)[0, 1]) * 100

    if risk_score <= 30:
        risk_level = "low"
    elif risk_score <= 55:
        risk_level = "medium"
    elif risk_score <= 75:
        risk_level = "high"
    else:
        risk_level = "critical"

    return TurnoverResponse(
        employee_id=req.employee_id,
        risk_score=round(risk_score, 2),
        risk_level=risk_level,
        top_factors=_top_factors(_model, _feature_names),
    )
