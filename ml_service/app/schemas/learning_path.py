from typing import Optional
from pydantic import BaseModel, Field


class MissingSkill(BaseModel):
    skill_id: str
    gap: float
    importance_weight: float
    complexity_level: int = 2           # 1=Beginner, 2=Intermediate, 3=Advanced


class LearningResource(BaseModel):
    resource_id: str
    title: Optional[str] = None
    skill_id: str
    skill_level: str = "Intermediate"   # "Beginner" | "Intermediate" | "Advanced"
    duration_hours: float = 5.0
    resource_type: Optional[str] = None


class LearningPathRequest(BaseModel):
    employee_id: str
    job_role_id: str
    missing_skills: list[MissingSkill]
    available_resources: list[LearningResource]
    employee_avg_score: float = Field(default=50.0, ge=0, le=100)
    employee_courses_done: int = Field(default=0, ge=0)


class RecommendedItem(BaseModel):
    skill_id: str
    resource_id: str
    resource_title: Optional[str] = None
    predicted_completion_score: float
    priority: str                       # "high" | "medium" | "low"


class LearningPathResponse(BaseModel):
    employee_id: str
    job_role_id: str
    ordered_skills: list[str]           # skills sorted by importance desc
    recommendations: list[RecommendedItem]
    estimated_completion_hours: float
