from typing import Literal
from pydantic import BaseModel, Field


class SkillProficiency(BaseModel):
    skill_id: str
    proficiency: float = Field(ge=0, le=5)


class RoleRequirement(BaseModel):
    skill_id: str
    min_proficiency: float = Field(ge=0, le=5)
    importance_weight: float = Field(ge=0, le=1)


class SkillGapDetail(BaseModel):
    skill_id: str
    required: float
    current: float
    gap: float
    importance_weight: float
    status: Literal["met", "partial", "missing"]


class RoleFitRequest(BaseModel):
    employee_id: str
    job_role_id: str
    employee_skills: list[SkillProficiency]
    role_requirements: list[RoleRequirement]


class RoleFitResponse(BaseModel):
    employee_id: str
    job_role_id: str
    fit_score: int                  # 0–100
    readiness_level: Literal["ready", "near_ready", "needs_development", "not_ready"]
    matching_skills: list[str]
    missing_skills: list[str]
    skill_gaps: list[SkillGapDetail]
