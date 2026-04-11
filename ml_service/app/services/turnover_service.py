import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from app.config import settings
from app.schemas.turnover import TurnoverRequest, TurnoverResponse

_model = None
_scaler = None
_feature_names: list[str] = []

ATTENDANCE_MAP = {"normal": 0, "at_risk": 1, "critical": 2}


def _load() -> None:
    global _model, _scaler, _feature_names
    model_dir = Path(settings.MODEL_DIR)
    _model    = joblib.load(model_dir / "best_turnover_model.pkl")
    _scaler   = joblib.load(model_dir / "scaler.pkl")
    try:
        _feature_names = joblib.load(model_dir / "turnover_features.pkl")
    except FileNotFoundError:
        _feature_names = []


def _top_factors(model, feature_names: list[str], n: int = 3) -> list[str]:
    if hasattr(model, "feature_importances_") and feature_names:
        idx = np.argsort(model.feature_importances_)[::-1][:n]
        return [feature_names[i] for i in idx]
    return []


def predict_turnover(req: TurnoverRequest) -> TurnoverResponse:
    global _model, _scaler
    if _model is None:
        _load()

    row = {
        "commute_distance_km":      req.commute_distance_km,
        "tenure_days":              req.tenure_days,
        "role_fit_score":           req.role_fit_score,
        "absence_rate":             req.absence_rate,
        "late_arrivals_30d":        req.late_arrivals_30d,
        "leave_requests_90d":       req.leave_requests_90d,
        "satisfaction_score":       req.satisfaction_score,
        "attendance_status_encoded": ATTENDANCE_MAP[req.attendance_status],
    }

    # Build a single-row DataFrame — use saved feature order if available
    X = pd.DataFrame([row])
    if _feature_names:
        # Keep only known features, add missing ones as 0, reorder
        for col in _feature_names:
            if col not in X.columns:
                X[col] = 0
        X = X[_feature_names]

    X_scaled    = _scaler.transform(X)
    risk_score  = float(_model.predict_proba(X_scaled)[0, 1]) * 100

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
