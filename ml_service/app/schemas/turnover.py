from typing import Literal
from pydantic import BaseModel, Field


class TurnoverRequest(BaseModel):
    employee_id: str
    commute_distance_km: float = Field(ge=0)
    tenure_days: int = Field(ge=0)
    role_fit_score: float = Field(ge=0, le=100)
    absence_rate: float = Field(ge=0, le=1)
    late_arrivals_30d: int = Field(ge=0)
    leave_requests_90d: int = Field(ge=0)
    satisfaction_score: float = Field(ge=0, le=100)
    attendance_status: Literal["normal", "at_risk", "critical"]


class TurnoverResponse(BaseModel):
    employee_id: str
    risk_score: float        # 0–100
    risk_level: Literal["low", "medium", "high", "critical"]
    top_factors: list[str]
